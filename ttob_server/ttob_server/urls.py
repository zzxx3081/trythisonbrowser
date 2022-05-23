from django.contrib import admin
from django.urls import path
from ttob_app.views import * 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name="index"),
    path('list/', listimg, name="listimg"),
    path('user/', userimg, name="userimg"),
    path('login/', login, name="login"),
    path('register/', register, name="register"),
    path('container/gcc/latest/', container, name="container"),
    path('container/ubuntu/18.04/', container_u, name="container_u"),
    path('container/centos/7/', container_c, name="container_c"),
    path('pro/', upgradepro, name="upgradepro"),
    path('install/dockerfile', dockerfile, name="dockerfile"),
    path('install/script', script, name="script"),
]

if settings.DEBUG:
  urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)