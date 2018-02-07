from __future__ import absolute_import

from datetime import timedelta

CELERY_IMPORTS = (
    'jobs.etl',
    'jobs.kobo',
)

CELERY_TIMEZONE = 'America/Mexico_City'
CELERY_ENABLE_UTC = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']

CELERYBEAT_SCHEDULE = {
    # http://docs.celeryproject.org/en/latest/reference/celery.schedules.html
    'etl_actions': {
        'task': 'etl_actions',
        'schedule': timedelta(seconds=60 * 5),
    },

    'sync_submissions': {
        'task': 'sync_submissions',
        'schedule': timedelta(seconds=60 * 10),
    },
    'upload_recent_submission_images': {
        'task': 'upload_recent_submission_images',
        'schedule': timedelta(seconds=60 * 10),
    },
}
