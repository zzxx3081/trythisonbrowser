from django.db import models
from django.conf import settings
from django.db.models import UniqueConstraint
from django.db.models.signals import post_save
from django.dispatch import receiver
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

class TaggedOpenSource(TaggedItemBase):
    content_object = models.ForeignKey('OpenSource', on_delete=models.CASCADE)

class OpenSource(models.Model):
    fullname = models.CharField(max_length=100, primary_key=True)
    author = models.CharField(blank=False, null=False, max_length=255)
    projectname = models.CharField(blank=False, null=False, max_length=255)
    tag = models.CharField(blank=False, null=False, max_length=255)
    contact = models.EmailField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=False, null=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="opensource_likes", blank=True)
    dislikes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="opensource_dislikes", blank=True)
    tags = TaggableManager(through=TaggedOpenSource, blank=True)

    def total_likes(self):
        return self.likes.count()

    def total_dislikes(self):
        return self.dislikes.count()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['projectname', 'tag'], name='pair')
        ]

class Dockerfile(models.Model):
	file = models.FileField(blank=False, null=False)

class InstalltionScript(models.Model):
    baseos = models.CharField(max_length=255)
    installationScript = models.TextField()

class Comment(models.Model):
    comment = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    opensource = models.ForeignKey(OpenSource, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class PortMap(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    opensource = models.ForeignKey(OpenSource, on_delete=models.CASCADE, null=True)
    portnum = models.CharField(blank=False, null=False, max_length=10)

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    port = models.IntegerField(blank=False, null=False, default=-1)
    opensource = models.CharField(max_length=50) 

    @receiver(post_save, sender=settings.AUTH_USER_MODEL)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=settings.AUTH_USER_MODEL)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()
