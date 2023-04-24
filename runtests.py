import os, sys, django, importlib.util

from django.conf import settings
from django.test.runner import DiscoverRunner

pkg_spec = importlib.util.spec_from_file_location("pb_djworkflow", "./src/pb_djworkflow/__init__.py")
pkg = importlib.util.module_from_spec(pkg_spec)
sys.modules['pb_djworkflow'] = pkg

test_pkg_spec = pkg_spec = importlib.util.spec_from_file_location("pb_djworkflow_tests", "./tests/pb_djworkflow_tests/__init__.py")
test_pkg = importlib.util.module_from_spec(test_pkg_spec)
sys.modules['pb_djworkflow_tests'] = test_pkg

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
        'pb_djworkflow_tests'
    )
)

django.setup()

TEST_RUNNER = DiscoverRunner(verbosity=1)
failures = TEST_RUNNER.run_tests(['pb_djworkflow_tests',], verbosity=1)

if failures:
    sys.exit(failures)