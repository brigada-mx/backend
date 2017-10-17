from django.utils import timezone

from celery import shared_task


@shared_task(name='etl_read_data')
def etl_read_data():
    pass
