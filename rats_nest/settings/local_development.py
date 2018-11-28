from .base import *
#import dj_database_url

DEBUG = True

ALLOWED_HOSTS = ['*']

SECRET_KEY = 'CHANGE_ME'

TIME_ZONE = 'UTC'
# TIME_ZONE = 'US/Pacific'

# DATABASES['default'] = dj_database_url.config(conn_max_age=600)

django_heroku.settings(locals())

print('local development settings loaded')
print('DATABASES = ' + str(DATABASES))
print('DATABASEURL = ' + str(os.environ.get('DATABASE_URL')))