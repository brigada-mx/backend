# flake8: noqa
from config.settings.base import *

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
