# flake8: noqa
from config.settings.base import *

ENVIRONMENT = 'development'
RAVEN_CONFIG['environment'] = 'development'

# https://github.com/tomchristie/django-pdb
INSTALLED_APPS = ['django_pdb',] + INSTALLED_APPS + ['debug_toolbar', 'django_extensions']

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django_pdb.middleware.PdbMiddleware',
]

DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = True

# shell_plus from django-extensions
SHELL_PLUS_PRE_IMPORTS = (
    ('django.core.urlresolvers', ('resolve',)),
)

SHELL_PLUS_POST_IMPORTS = (
)

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('CUSTOM_DATABASE_NAME'),
        'USER': os.getenv('CUSTOM_DATABASE_USER'),
        'PASSWORD': os.getenv('CUSTOM_DATABASE_PASSWORD'),
        'HOST': os.getenv('CUSTOM_DATABASE_HOST'),
        'PORT': os.getenv('CUSTOM_DATABASE_PORT'),
    }
}

REDIS_URL = 'redis://{host}:{port}/{database}'.format(
    host=os.getenv('CUSTOM_REDIS_HOST'),
    port=os.getenv('CUSTOM_REDIS_PORT'),
    database=os.getenv('CUSTOM_REDIS_DATABASE'),
)
CELERY_RESULT_BACKEND = REDIS_URL
BROKER_URL = REDIS_URL

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'cache_',
    },
}

# https://github.com/ottoyiu/django-cors-headers
CORS_ORIGIN_REGEX_WHITELIST = [r'^.*$',]

ALLOWED_HOSTS = ['*']
