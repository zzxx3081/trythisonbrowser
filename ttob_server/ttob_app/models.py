from django.db import models
from django.db.models import UniqueConstraint

class OpenSource(models.Model):
    author = models.CharField(blank=False, null=False, max_length=255)
    projectname = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    contact = models.EmailField(max_length=255, blank=True, null=True)
    description = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
	# osstype = models.ForeignKey("OpenSource", related_name="osstype", on_delete=models.CASCADE, db_column="opensource")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['projectname', 'tag'], name='pair')
        ]

class Dockerfile(models.Model):
	file = models.FileField(blank=False, null=False)

class InstalltionScript(models.Model):
    baseos = models.CharField(max_length=255)
    installationScript = models.TextField()


# Type:OpenSource = 1:N
# class OSSType(models.Model):
# 	opensource = models.ForeignKey("OpenSource", related_name="osstype", on_delete=models.CASCADE, db_column="opensource")
#     contents = models.TextField(help_text="Open Source Field", blank=False, null=False)

#     def __str__(self):
#         return '{}'.format(self.contents)	