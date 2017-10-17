from __future__ import absolute_import

from celery import Celery
from django.conf import settings

celery_app = Celery('mu')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
celery_app.config_from_object('django.conf:settings')
celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
