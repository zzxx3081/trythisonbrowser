from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import OpenSource, Dockerfile, InstalltionScript, Comment
from .forms import UserForm
import docker, sys, os, io, subprocess, time, threading, psutil
from django.conf import settings
from pathlib import Path

# registry url
BASE_URL = 'http://127.0.0.1:5000/'
TAG_PREFIX = 'localhost:5000/'

# initialize docker SDK
# docker must be installed
client = docker.from_env()

ps_table = []

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

def container_v1(request, fullname):

    open_source = get_object_or_404(OpenSource, fullname=fullname)
    ttydports = "netstat -taunp | grep ttyd | awk '{print $4}' | awk -F ':' '{print $2}'"
    startshell = "./ttyd.x86_64 -p 0 docker run -it localhost:5000/" + open_source.projectname + ":"  + open_source.tag    
    # startshell = "./ttyd.x86_64 -p 0 docker run -it " + open_source.projectname + ":"  + open_source.tag    

    print("==========================")
    print("the process is running")

    ### critical section ###

    # current opened port
    proc = subprocess.Popen(ttydports, shell=True, stdout=subprocess.PIPE, encoding='utf-8')
    output = proc.communicate()[0]
    old_used_port = list(dict.fromkeys(output.strip().splitlines()))
    if ('' in old_used_port):
        old_used_port.remove('')
    old_used_port = set(old_used_port)
    print(old_used_port)
    print("how many ports? : ", len(old_used_port))

    # start ttyd process
    process = subprocess.Popen(startshell, shell=True, stdout=subprocess.PIPE, encoding='utf-8')
    print(">>>>>>>>>>>>>process id :",process.pid)
    # newly added port
    proc = subprocess.Popen(ttydports, shell=True, stdout=subprocess.PIPE, encoding='utf-8')

    output = proc.communicate()[0]
    new_used_port = list(dict.fromkeys(output.strip().splitlines()))
    if ('' in new_used_port):
        new_used_port.remove('')
    print(new_used_port)    
    new_used_port = set(new_used_port)

    port = new_used_port - old_used_port
    port = list(port)[0]
    print(port)
    ### End critical section ###

    # ps_table.append(process.pid)
    # for pid in ps_table:
    #     print("killing process!!!!!!!!!!!!!!!!")
    #     if psutil.pid_exists(pid) == False:
    #         for child in pid.children(recursive=True):
    #             child.kill()
    #         pid.kill()
    #     else: 
    #         pass

    ## ttydports duplicate port?

    print("==========================")

    # out = subprocess.check_output(['./ttyd.x86_64', '-p', '0', 'docker', 'run', '-it', 'localhost:5000/ubuntu:18.04'])
    # print(out)
    return render(request, 'container.html', {'open_source':open_source, 'port':port})


def container(request, fullname):
    open_source = get_object_or_404(OpenSource, fullname=fullname)
    comments = Comment.objects.filter(opensource = fullname)
    ttydports = "netstat -taunp | grep ttyd | awk '{print $4}' | awk -F ':' '{print $2}'"
    startshell = "./ttyd.x86_64 -p 0 docker run -it localhost:5000/" + open_source.projectname + ":"  + open_source.tag    

    if request.method == 'POST':
        comment = request.POST['comment']
        opensource = open_source
        user = request.user
        Comment.objects.create(comment=comment, opensource=open_source, user=user)
        comments = Comment.objects.filter(opensource = fullname)

    else:

        ### critical section ###

        # current opened port
        proc = subprocess.Popen(ttydports, shell=True, stdout=subprocess.PIPE, encoding='utf-8')
        output = proc.communicate()[0]
        old_used_port = list(dict.fromkeys(output.strip().splitlines()))
        if ('' in old_used_port):
            old_used_port.remove('')
        # start ttyd process
        process = subprocess.Popen(startshell, shell=True, stdout=subprocess.PIPE, encoding='utf-8')

        # newly added port
        proc = subprocess.Popen(ttydports, shell=True, stdout=subprocess.PIPE, encoding='utf-8')

        output = proc.communicate()[0]
        new_used_port = list(dict.fromkeys(output.strip().splitlines()))
        if ('' in new_used_port):
            new_used_port.remove('')
        print("new used port : ", new_used_port)
        # select port which is not in old_used_port 


        # allocate port to user, 

        ### End critical section ###

    return render(request, 'container.html', {'open_source':open_source, 'comments':comments})


def userimg(request):
    return render(request, 'user.html')

def login(request):
    return render(request, 'login.html')

def register(request):
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


