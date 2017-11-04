import csv
from dateutil.parser import parse

from celery import shared_task
import pygsheets

from db.map.models import Locality, Organization, Action, ActionLog


@shared_task(name='etl_read_data')
def etl_read_data():
    pass
