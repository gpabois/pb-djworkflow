from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='pb-djworkflow',
    version='0.0.1',
    description="Another django workflow",
    author="Gaël Pabois",
    package_dir={'': 'src'},
    install_requires=[
        "Django>=4.2",
        "django-celery-results>=2.5.0",
        "celery>=5.2.7",
        "graphql_relay>=3.2.0",
        "graphene_django>=3.0.0",
        "django-filter==23.1",
        "graphene_file_upload>=1.3.0"
        "pb-graphene>=0.0.2"
    ]
)