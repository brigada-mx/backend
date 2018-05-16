from __future__ import absolute_import

from celery.schedules import crontab
from datetime import timedelta

CELERY_IMPORTS = (
    'jobs.kobo',
    'jobs.files',
    'jobs.discourse',
    'jobs.notifications',
)

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

    'sync_submissions_image_meta': {
        'task': 'sync_submissions_image_meta',
        'schedule': crontab(hour=[3+5]),
        'args': (None,),
    },
    'sync_submissions_image_meta_last_hour': {
        'task': 'sync_submissions_image_meta',
        'schedule': timedelta(seconds=60 * 5),
        'args': (1,),
    },

    'discourse_log_out_users': {
        'task': 'discourse_log_out_users',
        'schedule': crontab(minute=[15, 45], hour=3+5, day_of_month=[1, 15]),
    },

    'send_email_notifications_monday': {
        'task': 'send_email_notifications',
        'schedule': crontab(minute=30, hour=18+5, day_of_week=1),
    },
    'send_email_notifications': {
        'task': 'send_email_notifications',
        'schedule': crontab(minute=30, hour=[10+5, 14+5, 18+5], day_of_week=[2, 3, 4]),
    },
}
