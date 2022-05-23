from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def listimg(request):
    return render(request, 'list.html')

def userimg(request):
    return render(request, 'user.html')

def login(request):
    return render(request, 'login.html')

def register(request):
    return render(request, 'register.html')

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

def upgradepro(request):
    return render(request, 'upgradepro.html')