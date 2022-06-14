from django.contrib import admin
from django.urls import path, include
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
    path('container/<str:fullname>/', container, name="container"),
    path('install/dockerfile', dockerfile, name="dockerfile"),
    path('install/script', script, name="script"),
    path('setting/', setting, name="setting"),
    path('logout/', logout, name="logout"),
    path('delete/<str:username>', delete, name="delete"),
    path('like/<str:fullname>', LikeView, name="like"),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
  urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)