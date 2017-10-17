from config.settings.base import *

SITE_URL = "http://{}".format(SITE_URL_WITHOUT_SCHEME)

# https://github.com/tomchristie/django-pdb
INSTALLED_APPS = ('django_pdb',) + INSTALLED_APPS

INSTALLED_APPS += (
    'debug_toolbar',
    'django_extensions',
)

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django_pdb.middleware.PdbMiddleware',
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# Used for payments and other transactions that should not be real except in production
SANDBOX = True

COLLECTFAST_ENABLED = False

def show_toolbar(request):
    return True
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_toolbar,
}

DEBUG_PROPAGATE_EXCEPTIONS = True

# shell_plus from django-extensions
SHELL_PLUS_PRE_IMPORTS = (
    ('django.core.urlresolvers', ('resolve',)),
)

SHELL_PLUS_POST_IMPORTS = (
)

AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = '{}.s3.amazonaws.com'.format(AWS_STORAGE_BUCKET_NAME)

AWS_ACCESS_KEY_ID = os.getenv('CUSTOM_AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('CUSTOM_AWS_SECRET_KEY')
