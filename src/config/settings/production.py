# flake8: noqa
from config.settings.base import *

DEBUG = False
# ensures gunicorn prints full stack traces to logs
# https://docs.djangoproject.com/en/1.11/ref/settings/#debug-propagate-exceptions
DEBUG_PROPAGATE_EXCEPTIONS = True

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

REDIS_URL = f"redis://{os.getenv('CUSTOM_REDIS_URL')}/0"
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

# https://github.com/ottoyiu/django-cors-headers#cors_origin_whitelist
CORS_ORIGIN_WHITELIST = []

ALLOWED_HOSTS = ['*']
