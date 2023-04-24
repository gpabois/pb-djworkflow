import os
import sys
from django.conf import settings

if __name__ == "__main__":
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'pb_djworkflow',
            "tests"            
        ]
    )
    from django.core.management import execute_from_command_line
    args = sys.argv + ["makemigrations", "pb_djworkflow", "tests"]
    execute_from_command_line(args)