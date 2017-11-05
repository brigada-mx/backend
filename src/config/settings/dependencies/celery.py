from __future__ import absolute_import

from datetime import timedelta
from celery.schedules import crontab

CELERY_IMPORTS = (
    'jobs.etl',
)

CELERY_TIMEZONE = 'America/Mexico_City'
CELERY_ENABLE_UTC = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']

CELERYBEAT_SCHEDULE = {
    # http://docs.celeryproject.org/en/latest/reference/celery.schedules.html

    ##########
    # ETL
    ##########
    'etl_localities': {
        'task': 'etl_localities',
        'schedule': crontab(minute=0, hour=[2, 4])
    },
    'etl_actions': {
        'task': 'etl_actions',
        'schedule': timedelta(seconds=60 * 15),
    },

}
