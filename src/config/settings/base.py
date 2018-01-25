# flake8: noqa
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ADMINS = (
    ('Kyle Bebak', 'kylebebak@gmail.com'),
)

SECRET_KEY = os.getenv('CUSTOM_SECRET_KEY')


DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('CUSTOM_DATABASE_NAME'),
        'USER': os.getenv('CUSTOM_DATABASE_USER'),
        'PASSWORD': os.getenv('CUSTOM_DATABASE_PASSWORD'),
        'HOST': os.getenv('CUSTOM_DATABASE_HOST'),
        'PORT': os.getenv('CUSTOM_DATABASE_PORT')
    }
}

INSTALLED_APPS = [
    # built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    # project apps
    'db.users',
    'db.map',
    'helpers',
    'jobs',
    'api',

    # third-party apps
    'rest_framework',
    'corsheaders',
    'django_filters',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTH_USER_MODEL = 'users.StaffUser'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

ROOT_URLCONF = 'config.urls'

# DON'T REMOVE context processors, this could introduce a lot of subtle bugs
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


LANGUAGE_CODE = 'es-MX'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_URL = '/static/'


REDIS_URL = 'redis://:{password}@{host}:{port}/{database}'.format(
    password=os.getenv('CUSTOM_REDIS_PASSWORD'),  # make sure password is URL safe
    host=os.getenv('CUSTOM_REDIS_HOST'),
    port=os.getenv('CUSTOM_REDIS_PORT'),
    database=os.getenv('CUSTOM_REDIS_DATABASE'),
)
CELERY_RESULT_BACKEND = REDIS_URL
BROKER_URL = REDIS_URL



CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{host}:{port}/{database}'.format(
            host=os.getenv('CUSTOM_REDIS_HOST'),
            port=os.getenv('CUSTOM_REDIS_PORT'),
            database=os.getenv('CUSTOM_REDIS_DATABASE'),
        ),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.getenv('CUSTOM_REDIS_PASSWORD'),
        },
        'KEY_PREFIX': 'cache_',
    },
}


# list of origin hostnames that are authorized to make cross-site HTTP requests
# https://github.com/ottoyiu/django-cors-headers#cors_origin_whitelist
CORS_ORIGIN_WHITELIST = (
    '919.local.mx:8080',
    '919.local.mx:8081',
)

CORS_ALLOW_METHODS = (
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
)

SITE_URL_WITHOUT_SCHEME = os.getenv('CUSTOM_SITE_URL')
SITE_URL = 'https://{}'.format(SITE_URL_WITHOUT_SCHEME)
LOCAL_API_URL = os.getenv('CUSTOM_API_HOST')
ALLOWED_HOSTS = [SITE_URL_WITHOUT_SCHEME, LOCAL_API_URL, os.getenv('CUSTOM_NGROK_HOST')]

# contact info
CONTACT_PHONE = os.getenv('CUSTOM_CONTACT_PHONE')
CONTACT_EMAIL = os.getenv('CUSTOM_CONTACT_EMAIL')
CONTACT_ADDRESS = os.getenv('CUSTOM_CONTACT_ADDRESS')

# settings for dependencies (keep at the end of file)
from config.settings.dependencies.celery import *
from config.settings.dependencies.rest_framework import *
