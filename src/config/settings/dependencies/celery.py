from __future__ import absolute_import

from datetime import timedelta

CELERY_IMPORTS = (
    'jobs.etl',
    'jobs.kobo',
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
    'etl_actions': {
        'task': 'etl_actions',
        'schedule': timedelta(seconds=60 * 15),
    },
    'etl_submissions': {
        'task': 'etl_submissions',
        'schedule': timedelta(seconds=60 * 15),
    },
    'upload_recent_submission_images': {
        'task': 'upload_recent_submission_images',
        'schedule': timedelta(seconds=60 * 15),
    },

}
