from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Process)
admin.site.register(models.Task)