import os
import pb_djworkflow

from celery import Celery
import celery.contrib.testing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_celery.settings")
os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

app = Celery("pb_djworkflow_tests")
app.config_from_object("django.conf:settings")
app.autodiscover_tasks([
    'pb_djworkflow', 
    'celery.contrib.testing'
    ], force=True
)