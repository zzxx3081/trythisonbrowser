from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, TemplateView
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

class TagCloudTV(TemplateView):
    template_name = 'taggit/taggit_cloud.html'


class TaggedObjectLV(ListView):
    template_name = 'taggit/taggit_post_list.html'
    model = OpenSource

    def get_queryset(self):
        return OpenSource.objects.filter(tags__name=self.kwargs.get('tag'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tagname'] = self.kwargs['tag']
        return context

def LikeView(request, fullname):
    print("into views")
    print(fullname)
    opensource = get_object_or_404(OpenSource, fullname=fullname)
    
    re = opensource.likes.filter(username=request.user.username)
    
    if re.exists():
        opensource.likes.remove(request.user)
    else:
        opensource.likes.add(request.user)

    return HttpResponseRedirect(reverse('container', args=[fullname]))

def about(request):
    return render(request, 'about.html')

def index(request):
    # show 5 recent opensources
    recent = OpenSource.objects.all().order_by('-uploaded_at')[:5]

    unsorted_results = OpenSource.objects.all()
    popular = sorted(unsorted_results, key= lambda t: t.total_likes(), reverse=True)[0:3]

    if request.user.is_authenticated:
        u = User.objects.get(username=request.user.username)
        open_sources = u.opensource_likes.all()

        user_liked_tag = []

        print("user liked tags")
        for open_source in open_sources:
            os_tags = open_source.tags.all()
            for tags in os_tags:
                user_liked_tag.append(tags.name)

        user_liked_tags = list(set(user_liked_tag))
        print(user_liked_tags)
        user_liked_tagged_open_source = OpenSource.objects.filter(tags__name__in=user_liked_tag).distinct()[0:5]
        
        if user_liked_tagged_open_source.exists():
            recommend = True
        else:
            recommend = False

        print("tagged opensource")
        print(user_liked_tagged_open_source)

        return render(request, 'index.html', {'recent':recent, 'popular':popular, 'user_liked_tagged_open_source':user_liked_tagged_open_source})
    else:
        return render(request, 'index.html', {'recent':recent, 'popular':popular})

def listimg(request):
    # get all open source images
    open_sources = OpenSource.objects.all().order_by('-uploaded_at')
    
    if request.method == 'POST':
        searchword = request.POST['searchword']
        open_sources = OpenSource.objects.filter(projectname=searchword.lower()).order_by('-uploaded_at')
        ## TODO advanced search: captical words ... 

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
        url = BASE_URL + ":" + str(profile.port)
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
            ##### get port END CRITICAL SECTION #####

            if profile.port == -1:
                profile.port = port
                profile.save()
            else:                
                ##### get port CRITICAL SECTION #####
                os.system("fuser -k " + str(profile.port) + "/tcp")
                ##### get port END CRITICAL SECTION #####
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


def user(request):
    u = User.objects.get(username=request.user.username)
    open_sources = u.opensource_likes.all()

    return render(request, 'user.html', {'open_sources':open_sources})


def DeleteView(request, fullname):
    opensource = get_object_or_404(OpenSource, fullname=fullname)
    opensource.likes.remove(request.user)
    return HttpResponseRedirect(reverse('user'))

@login_required(login_url="/login/")
def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(
            request, username=username, password=password
        )

        if user is not None:
            auth.login(request, user)
            return redirect('index')
        else:
            return render(request, "login.html", {
                'error': 'Username or Password is incorrect.',
            })
    else:
        return render(request, "login.html")

        
def register(request):
    ## TODO/Exception Handling:duplicate username 
    if request.method == 'POST':
        form = UserForm(request.POST)
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
                auth.login(request, user, backend='django.contrib.auth.backends.ModelBackend')  
                return redirect('/')
            except IntegrityError:
                messages.warning(request, "Already registered")
                return render(request, 'register.html', {'form': form})        
            
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
        hashtags = request.POST.get('hashtag', '').split(',')

        registry_tag = TAG_PREFIX + projectname + ":" + tag
        fullname = projectname + ":" + tag
        try:
            opensource = OpenSource.objects.create(fullname=fullname, author=author, projectname=projectname, tag=tag, contact=contact, description=description)
            for hashtag in hashtags:
                hashtag = hashtag.strip()
                opensource.tags.add(hashtag)
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
        hashtags = request.POST.get('hashtag', '').split(',')

        registry_tag = TAG_PREFIX + projectname + ":" + tag
        fullname = projectname + ":" + tag
        baseos = request.POST['baseos']
        installationscript = request.POST['installationscript']
        
        try:
            opensource = OpenSource.objects.create(fullname=fullname, author=author, projectname=projectname, tag=tag, contact=contact, description=description)
            for hashtag in hashtags:
                hashtag = hashtag.strip()
                opensource.tags.add(hashtag)
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


