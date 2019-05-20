import dj_database_url, logging
from .base import *

logger = logging.getLogger(__name__)

ALLOWED_HOSTS = ['rats-nest-1442.herokuapp.com']

SECRET_KEY = os.environ.get('SECRET_KEY')

DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.postgresql_psycopg2'
     }
}

DATABASES['default'].update(dj_database_url.config())  # now working on remote heroku !!!

# Caches (largely for select2)
CACHES = {
    'default': {
        'BACKEND': 'django_bmemcached.memcached.BMemcached',
        'LOCATION': os.environ.get('MEMCACHEDCLOUD_SERVERS').split(','),
        'TIMEOUT': 60 * 60 * 24,  # secs * minutes * hours = 1 day
        'OPTIONS': {
                    'username': os.environ.get('MEMCACHEDCLOUD_USERNAME'),
                    'password': os.environ.get('MEMCACHEDCLOUD_PASSWORD')
            }
    }
}

logger.info('heroku_production settings loaded')
