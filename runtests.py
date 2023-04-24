import os, sys, django
from django.conf import settings
from django.test.runner import DiscoverRunner

DIRNAME = os.path.dirname(__file__)

settings.configure(
    DEBUG = True,
    DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField',
    TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner',
    DATABASES={
        'default': {
            'ENGINE':  'django.db.backends.postgresql_psycopg2',
            'USER': 'test',
            'PASSWORD': 'test',
            'HOST': 'localhost',
            'NAME': 'pb_workflow_engine'
        }
    },
    CELERY_RESULT_BACKEND = 'django-db',
    CELERY_CACHE_BACKEND = 'django-cache',
    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django_celery_results',
        'pb_djworkflow',
        'tests'
    )
)

django.setup()

TEST_RUNNER = DiscoverRunner(verbosity=1)
failures = TEST_RUNNER.run_tests(['tests',], verbosity=1)

if failures:
    sys.exit(failures)