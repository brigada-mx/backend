# flake8: noqa
from config.settings.base import *

DEBUG = False
SANDBOX = False

# ensures gunicorn prints full stack traces to logs
DEBUG_PROPAGATE_EXCEPTIONS = True

# AWS S3
AWS_HEADERS = {  # see http://developer.yahoo.com/performance/rules.html#expires
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'Cache-Control': 'max-age={}'.format(3600),
}

HOME = '/home/custom'
