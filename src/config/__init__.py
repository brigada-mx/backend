# flake8: noqa
"""Don't mess with the imports in this file, it exports things that are imported
from config in other modules.
"""
from __future__ import absolute_import
from .celery_app import celery_app
