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

DATABASES['default'] = dj_database_url.parse('postgres://rats_user:RatFriends420@localhost/rats_database',
                                              conn_max_age=600)

# largely for select2

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        'LOCATION': 'localhost:11211',
        'TIMEOUT': 1200,  # 1200 seconds = 20 minutes
    }
}

logger.info('local development settings loaded')
