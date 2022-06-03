from django.contrib import admin
from .models import OpenSource, Dockerfile
# Register your models here.


admin.site.register(OpenSource)
admin.site.register(Dockerfile)