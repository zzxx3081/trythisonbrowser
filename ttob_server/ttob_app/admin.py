from django.contrib import admin
from .models import OpenSource, Dockerfile, InstalltionScript, Comment
# Register your models here.


admin.site.register(OpenSource)
admin.site.register(Dockerfile)
admin.site.register(InstalltionScript)
admin.site.register(Comment)
