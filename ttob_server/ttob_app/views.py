from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import OpenSource, Dockerfile, InstalltionScript, Comment, Profile
from .forms import UserForm
import docker, sys, os, io, subprocess, time, threading, psutil
from django.conf import settings
from pathlib import Path

# registry url
BASE_URL = 'http://127.0.0.1'
TAG_PREFIX = 'localhost:5000/'

# initialize docker SDK
# docker must be installed
client = docker.from_env()

ps_table = []

def LikeView(request, fullname):
    print("into views")
    print(fullname)
    opensource = get_object_or_404(OpenSource, fullname=fullname)
    print("hello")
    opensource.likes.add(request.user)
    return HttpResponseRedirect(reverse('container', args=[fullname]))

def list_duplicates(seq):
  seen = set()
  seen_add = seen.add
  # adds all elements it doesn't know yet to seen and all other to seen_twice
  seen_twice = set( x for x in seq if x in seen or seen_add(x) )
  # turn the set into a list (as requested)
  return list( seen_twice )

def index(request):
    return render(request, 'index.html')

def listimg(request):
    # get all open source images
    open_sources = OpenSource.objects.all()
    ## TODO pagination 

    return render(request, 'list.html', {'open_sources':open_sources})


@login_required
def container(request, fullname):
    open_source = get_object_or_404(OpenSource, fullname=fullname)
    total_likes = open_source.total_likes()
    comments = Comment.objects.filter(opensource=fullname)
    listports = "netstat -taunp | grep ttyd | awk '{print $4}' | awk -F ':' '{print $2}'"
    startshell = "./ttyd.x86_64 -p 0 docker run -it localhost:5000/" + open_source.projectname + ":"  + open_source.tag    
    user = request.user
    profile = get_object_or_404(Profile, user=user)

    if request.method == 'POST':
        comment = request.POST['comment']
        opensource = open_source
        Comment.objects.create(comment=comment, opensource=open_source, user=user)
        comments = Comment.objects.filter(opensource = fullname)
    else:
        # if request's user project is same as entered project 
        print("profile.opensource", profile.opensource)
        print("open_source.fullname", open_source.fullname)
        
        if profile.opensource != open_source.fullname:
            profile.opensource = open_source.fullname
            profile.save()

            ##### get port CRITICAL SECTION #####
            output = subprocess.Popen(listports, shell=True, stdout=subprocess.PIPE, encoding='utf-8').communicate()[0]

            old_used_port = list(dict.fromkeys(output.strip().splitlines()))
            if ('' in old_used_port):
                old_used_port.remove('')

            # start ttyd process
            process = subprocess.Popen(startshell, shell=True, stdout=subprocess.PIPE, encoding='utf-8')

            # newly added port
            output = subprocess.Popen(listports, shell=True, stdout=subprocess.PIPE, encoding='utf-8').communicate()[0]

            new_used_port = list(dict.fromkeys(output.strip().splitlines()))
            if ('' in new_used_port):
                new_used_port.remove('')
            
            print("new used port as list : ", new_used_port)
            port = list(set(new_used_port) - set(old_used_port))[0]
            print("port" , port)
            #### get port end ####

            # release previous port - if profile.port == -1: pass, else: release profile.port
            if profile.port == -1:
                profile.port = port
                profile.save()
            else:                
                os.system("fuser -k " + str(profile.port) + "/tcp")
                profile.port = port
                profile.save()

            url = BASE_URL + ":" + port
        else:
            print("passing .................... ")
            output = subprocess.Popen(listports, shell=True, stdout=subprocess.PIPE, encoding='utf-8').communicate()[0]

            new_used_port = list(dict.fromkeys(output.strip().splitlines()))
            if ('' in new_used_port):
                new_used_port.remove('')
            
            print("new used port as list : ", new_used_port)

            url = BASE_URL + ":" + str(profile.port)

    return render(request, 'container.html', {'url':url, 'open_source':open_source, 'comments':comments, 'total_likes':total_likes})


def userimg(request):
    return render(request, 'user.html')

def login(request):


    return render(request, 'login.html')

def register(request):
    ## TODO/Exception Handling:duplicate username 
    if request.method == 'POST':
        form = UserForm(request.POST)
        if request.POST['password1'] == request.POST['password2']:
            user = User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
            auth.login(request, user, backend='django.contrib.auth.backends.ModelBackend')  
            return redirect('/')
        else: 
            messages.warning(request, "password doesn't match")
            return render(request, 'register.html', {'form': form})
    else:
        form = UserForm()
        return render(request, 'register.html', {'form': form})

def logout(request):
    auth.logout(request)
    return redirect('login')

@login_required(login_url="/login/")
def delete(request, username):
    if request.method == 'POST':
        context = {}
        try:
            u = User.objects.get(username=username)
            u.delete()
            context['msg'] = 'The user is deleted.'       
        except User.DoesNotExist: 
            context['msg'] = 'User does not exist.'
        except Exception as e: 
            context['msg'] = e.message
        finally:
            return redirect('login')

@login_required(login_url="/login/")
def setting(request):
    return render(request, 'setting.html')


@login_required(login_url="/login/")
def dockerfile(request):
    ## POST: build from dockerfile
    if request.method == 'POST':
        author = request.POST['author']
        projectname = request.POST['projectname']
        tag = request.POST['tag']
        contact = request.POST['contact']
        description = request.POST['description']
        registry_tag = TAG_PREFIX + projectname + ":" + tag
        fullname = projectname + ":" + tag
        try:
            OpenSource.objects.create(fullname=fullname, author=author, projectname=projectname, tag=tag, contact=contact, description=description)
            obj = Dockerfile.objects.create(file=request.FILES['dockerfile'])
            try:
                image = client.images.build(fileobj=obj.file, tag=registry_tag)
                # push image to registry
                for line in client.api.push(repository=registry_tag, stream=True, decode=True):
                    print(line)
                    print("INFO: image upload complete.")
            except Exception:
                messages.warning(request, 'Dockerfile Build Error')
                return render(request, 'install_dockerfile.html')
        except IntegrityError:
            messages.warning(request, 'Same Opensource has been already registered')
        finally:
            pass # TODO Remove tmp Dockerfile
        return render(request, 'install_dockerfile.html')
    else:
        return render(request, 'install_dockerfile.html')

@login_required(login_url="/login/")
def script(request):

    if request.method == 'POST':
        author = request.POST['author']
        projectname = request.POST['projectname']
        tag = request.POST['tag']
        contact = request.POST['contact']
        description = request.POST['description']
        registry_tag = TAG_PREFIX + projectname + ":" + tag
        fullname = projectname + ":" + tag
        baseos = request.POST['baseos']
        installationscript = request.POST['installationscript']
        
        try:
            OpenSource.objects.create(fullname=fullname, author=author, projectname=projectname, tag=tag, contact=contact, description=description)
            try:
                InstalltionScript.objects.create(baseos=baseos, installationScript=installationscript)
                f = open("Dockerfile", 'w')
                data = "FROM " + baseos + '\n'
                f.write(data)
                
                lines = installationscript.splitlines()
                for i in lines:
                    if i != "":
                        data = "RUN " + i + '\n'
                        f.write(data)
                f.close()

                image = client.images.build(path=os.getcwd(), tag=registry_tag)
                # push image to registry
                for line in client.api.push(repository=registry_tag, stream=True, decode=True):
                    print(line)
                    print("INFO: image upload complete.")
                return render(request, 'install_script.html')
            except Exception:
                messages.warning(request, 'Dockerfile Build Error')
            finally:
                file_path = os.getcwd() + '/Dockerfile'
                print("Dockerfile path : ", file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        except IntegrityError:
            messages.warning(request, 'Same Opensource has been already registered')
        return render(request, 'install_script.html')
    else:
        return render(request, 'install_script.html')


