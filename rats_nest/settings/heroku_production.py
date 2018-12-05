import os, django_heroku, dj_database_url
from .base import *

DEBUG = False

ALLOWED_HOSTS = ['rats-nest-420.herokuapp.com']

SECRET_KEY = os.environ.get('SECRET_KEY')


DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.postgresql_psycopg2'
     }
}

DATABASES['default'].update(dj_database_url.config()) # now working on remote heroku !!!

print('heroku_production settings loaded')