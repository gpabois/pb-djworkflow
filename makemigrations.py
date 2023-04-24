import os, sys, importlib.util
from django.conf import settings

pkg_spec = importlib.util.spec_from_file_location("pb_djworkflow", "./src/pb_djworkflow/__init__.py")
pkg = importlib.util.module_from_spec(pkg_spec)
sys.modules['pb_djworkflow'] = pkg

test_pkg_spec = pkg_spec = importlib.util.spec_from_file_location("pb_djworkflow_tests", "./tests/pb_djworkflow_tests/__init__.py")
test_pkg = importlib.util.module_from_spec(test_pkg_spec)
sys.modules['pb_djworkflow_tests'] = test_pkg

if __name__ == "__main__":
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'pb_djworkflow',
            'pb_djworkflow_tests'          
        ]
    )
    from django.core.management import execute_from_command_line
    args = sys.argv + ["makemigrations", "pb_djworkflow", "pb_djworkflow_tests"]
    execute_from_command_line(args)