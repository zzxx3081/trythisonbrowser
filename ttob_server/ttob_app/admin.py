from django.contrib import admin
from .models import OpenSource, Dockerfile, InstalltionScript, Comment, Profile
# Register your models here.


admin.site.register(OpenSource)
admin.site.register(Dockerfile)
admin.site.register(InstalltionScript)
admin.site.register(Comment)
admin.site.register(Profile)