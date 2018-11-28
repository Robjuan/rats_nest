from .base import *
import dj_database_url, os

DEBUG = True

ALLOWED_HOSTS = ['*']

SECRET_KEY = 'CHANGE_ME'

TIME_ZONE = 'UTC'
# TIME_ZONE = 'US/Pacific'

DATABASES['default'] = dj_database_url.parse('postgres://rats_user:RatFriends420@localhost/rats_database',
                                              conn_max_age=600)

print('local development settings loaded')

if os.environ.get('DEBUG'):
    print('DATABASES = ' + str(DATABASES))
