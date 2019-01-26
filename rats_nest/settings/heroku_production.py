import dj_database_url, logging
from .base import *

logger = logging.getLogger(__name__)

DEBUG = False
DEBUG_PROPAGATE_EXCEPTIONS = False

ALLOWED_HOSTS = ['rats-nest-420.herokuapp.com']

SECRET_KEY = os.environ.get('SECRET_KEY')


DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.postgresql_psycopg2'
     }
}

DATABASES['default'].update(dj_database_url.config())  # now working on remote heroku !!!

logger.info('heroku_production settings loaded')
