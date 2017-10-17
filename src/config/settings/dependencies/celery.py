from __future__ import absolute_import

from datetime import timedelta
from celery.schedules import crontab

# List of modules to import when celery starts.
CELERY_IMPORTS = (
    'jobs.etl',
)

CELERY_TIMEZONE = 'America/Mexico_City'
CELERY_ENABLE_UTC = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']

CELERYBEAT_SCHEDULE = {
    # http://docs.celeryproject.org/en/latest/reference/celery.schedules.html#celery.schedules.crontab.day_of_week

    ##########
    # ETL
    ##########
    'etl_read_data': {
        'task': 'etl_read_data',
        'schedule': timedelta(seconds=7200),
    },
    # 'etl_read_other_data': {
    #     'task': 'etl_read_other_data',
    #     'schedule': crontab(minute=0, hour=[2, 4, 6])
    #     # run this several times a day to ensure it isn't skipped
    # },

}
