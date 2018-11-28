import os, django_heroku
from .base import *

DEBUG = False

ALLOWED_HOSTS = ['rats-nest-420.herokuapp.com']

SECRET_KEY = os.environ.get('SECRET_KEY')


DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.postgresql_psycopg2'
     }
}

django_heroku.settings(locals())

print('heroku_production settings loaded')