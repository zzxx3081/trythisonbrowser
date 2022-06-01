from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import UserForm

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

def dockerfile(request):
    return render(request, 'install_dockerfile.html')

def script(request):
    return render(request, 'install_script.html')

@login_required(login_url="/login/")
def setting(request):
    return render(request, 'setting.html')

def logout(request):
    auth.logout(request)
    return redirect('login')

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