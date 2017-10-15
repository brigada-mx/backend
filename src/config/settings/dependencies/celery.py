from __future__ import absolute_import

from datetime import timedelta
from celery.schedules import crontab

# List of modules to import when celery starts.
CELERY_IMPORTS = (
    'message.notifications',
    'message.activityfeed',
    'message.maintenance',
)

CELERY_TIMEZONE = 'America/Mexico_City'
CELERY_ENABLE_UTC = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']

CELERYBEAT_SCHEDULE = {
    # http://docs.celeryproject.org/en/latest/reference/celery.schedules.html#celery.schedules.crontab.day_of_week

    ##########
    # STAFF
    ##########
    'notify_staff_checkin_delay': {
        'task': 'notify_staff_checkin_delay',
        'schedule': timedelta(seconds=300),
    },


    ##########
    # CLIENTS
    ##########
    # in general, clients don't need to be notified as frequently as nurses
    'notify_client_prepayment': {
        'task': 'notify_client_prepayment',
        'schedule': crontab(minute=0, hour=11)
    },
    'notify_client_pending_of_review': {
        'task': 'notify_client_pending_review',
        'schedule': crontab(minute=0, hour=10)
    },
    'notify_client_shift_time': {
        'task': 'notify_client_shift_time',
        'schedule': timedelta(seconds=600),
    },
    'notify_client_care_log': {
        'task': 'notify_client_care_log',
        'schedule': timedelta(seconds=1200),
    },
    'notify_client_recent_shifts': {
        'task': 'notify_client_recent_shifts',
        'schedule': timedelta(seconds=3600),
    },

    'activityfeed_client_shift_milestones': {
        'task': 'activityfeed_client_shift_milestones',
        'schedule': crontab(minute=0, hour=2) # perform this task daily, when there is minimal load on DB
    },
    'activityfeed_client_nurse_shift_milestones': {
        'task': 'activityfeed_client_nurse_shift_milestones',
        'schedule': crontab(minute=15, hour=2) # perform this task daily, when there is minimal load on DB
    },
    'activityfeed_client_shift_carelogentry_completion': {
        'task': 'activityfeed_client_shift_carelogentry_completion',
        'schedule': crontab(minute=[15,45], hour=6) # perform task in morning for shifts that finished the previous day
    },
    'activityfeed_client_weekly_carelogentry_completion': {
        'task': 'activityfeed_client_weekly_carelogentry_completion',
        'schedule': crontab(minute=[0,30], hour=6, day_of_week=1) # perform task once a week in morning for shifts that finished in the previous week
    },
    'activityfeed_client_weekly_patient_report': {
        'task': 'activityfeed_client_weekly_patient_report',
        'schedule': crontab(minute=[15,45], hour=5, day_of_week=1) # perform task once a week in morning for shifts that finished in the previous week
    },
    'send_client_carelog_report': {
        'task': 'send_client_carelog_report',
        'schedule': crontab(minute=0, hour=10, day_of_week=1)
    },


    ##########
    # NURSES
    ##########
    'notify_nurse_update_home_location': {
        'task': 'notify_nurse_update_home_location',
        'schedule': crontab(minute=30, hour=11, day_of_month=[1,15,]),
    },
    'notify_nurse_shift_time': {
        'task': 'notify_nurse_shift_time',
        'schedule': timedelta(seconds=450),
    },
    'notify_nurse_care_log_entry_time': {
        'task': 'notify_nurse_care_log_entry_time',
        'schedule': timedelta(seconds=600),
    },


    ##########
    # OTHER
    ##########
    'maintenance_reap_unsuccessful_reports': {
        'task': 'maintenance_reap_unsuccessful_reports',
        'schedule': timedelta(seconds=3600),
    },
    'maintenance_generate_shifts': {
        'task': 'maintenance_generate_shifts',
        'schedule': crontab(minute=0, hour=[2,4,6,]) # run this several times a day to ensure it isn't skipped
    },

}
