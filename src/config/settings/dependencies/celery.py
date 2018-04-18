from __future__ import absolute_import

from celery.schedules import crontab
from datetime import timedelta

CELERY_IMPORTS = (
    'jobs.kobo',
    'jobs.discourse',
)

CELERY_TIMEZONE = 'America/Mexico_City'
CELERY_ENABLE_UTC = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']

CELERYBEAT_SCHEDULE = {
    # http://docs.celeryproject.org/en/latest/reference/celery.schedules.html
    'sync_submissions': {
        'task': 'sync_submissions',
        'schedule': timedelta(seconds=60 * 10),
    },
    'upload_recent_submission_images': {
        'task': 'upload_recent_submission_images',
        'schedule': timedelta(seconds=60 * 10),
    },

    'discourse_log_out_users': {
        'task': 'discourse_log_out_users',
        'schedule': crontab(minute=[15, 45], hour=3, day_of_week=[1, 4]),
    },
}
