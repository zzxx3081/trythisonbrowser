from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import OpenSource, Dockerfile, InstalltionScript
from .forms import UserForm
import docker, os, io
from django.conf import settings
from pathlib import Path

# registry url
BASE_URL = 'http://127.0.0.1:5000/'
TAG_PREFIX = 'localhost:5000/'

# initialize docker SDK
# docker must be installed
client = docker.from_env()

def index(request):
    return render(request, 'index.html')

def listimg(request):
    return render(request, 'list.html')

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

def container(request):
    return render(request, 'container.html')

def container_u(request):
    return render(request, 'container_u.html')

def container_c(request):
    return render(request, 'container_c.html')

@login_required(login_url="/login/")
def dockerfile(request):
    ## POST: build from dockerfile
    if request.method == 'POST':
        author = request.POST['author']
        projectname = request.POST['projectname']
        tag = request.POST['tag']
        contact = request.POST['contact']
        description = request.POST['description']
        registry_tag = TAG_PREFIX + projectname + "_" + tag
        try:
            OpenSource.objects.create(author=author, projectname=projectname, tag=tag, contact=contact, description=description)
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
        registry_tag = TAG_PREFIX + projectname + "_" + tag
        baseos = request.POST['baseos']
        installationscript = request.POST['installationscript']
        
        try:
            OpenSource.objects.create(author=author, projectname=projectname, tag=tag, contact=contact, description=description)
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


@login_required(login_url="/login/")
def setting(request):
    return render(request, 'setting.html')

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