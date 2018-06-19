from __future__ import absolute_import

from django.conf import settings

from celery import Celery


celery_app = Celery('tasks')

celery_app.config_from_object('django.conf:settings')
celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
