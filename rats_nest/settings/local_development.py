# this shit requires the following environment variable:
# DJANGO_SETTINGS_MODULE=rats_nest.settings.local_development

from .base import *
import dj_database_url
import logging
logger = logging.getLogger(__name__)

DEBUG = True
#DEBUG_PROPAGATE_EXCEPTIONS = True


ALLOWED_HOSTS = ['*']

SECRET_KEY = 'CHANGE_ME'

TIME_ZONE = 'UTC'
# TIME_ZONE = 'US/Pacific'

DB_NAME = os.environ.get('DB_NAME')
DB_USERNAME = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

# first defined in base.py
DATABASES['default'] = dj_database_url.parse('postgres://'+DB_USERNAME+':'+DB_PASSWORD+'@localhost/'+DB_NAME,
                                             conn_max_age=600)

# largely for select2

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        'LOCATION': 'localhost:11211',
        'TIMEOUT': 60 * 60 * 24,  # secs * minutes * hours = 1 day
    }
}

logger.info('local development settings loaded')
