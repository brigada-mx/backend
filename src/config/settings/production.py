# flake8: noqa
from config.settings.base import *

DEBUG = False
# ensures gunicorn prints full stack traces to logs
# https://docs.djangoproject.com/en/1.11/ref/settings/#debug-propagate-exceptions
DEBUG_PROPAGATE_EXCEPTIONS = True
