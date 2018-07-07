from typing import Any
import json
import gzip

from django.db.models import Prefetch
from django.db import transaction, connection
from django.utils import timezone

from celery import shared_task
import requests

from helpers.http import get_s3_client, raise_for_status
from db.map.models import Action, Donation, Testimonial


def get_status_by_category(action, prefetched=False):
    d = {}

    d['desc'] = bool(action.desc)

    d['dates'] = bool(action.start_date and action.end_date)

    d['progress'] = bool(action.unit_of_measurement) \
        and action.target is not None and action.progress is not None

    d['budget'] = bool(action.budget)

    d['image_count'] = action.image_count

    if prefetched:
        d['testimonials'] = len(action.testimonials)
        d['donations'] = len(action.donations)
        d['verified_donations'] = len(action.verified_donations)
    else:
        d['testimonials'] = len(action.testimonial_set.filter(published=True))
        d['donations'] = len(action.donation_set.filter(approved_by_donor=True, approved_by_org=True))
        d['verified_donations'] = len(action.donation_set.filter(
            approved_by_donor=True, approved_by_org=True, donor__donoruser__isnull=False).distinct()
        )

    return d


def get_score(status_by_category):
    dates = status_by_category.get('dates', False)
    progress = status_by_category.get('progress', False)
    budget = status_by_category.get('budget', False)
    image_count = status_by_category.get('image_count', 0)
    testimonials = status_by_category.get('image_count', 0)
    donations = status_by_category.get('donations', 0)
    verified_donations = status_by_category.get('verified_donations', 0)

    return (image_count + testimonials * 5) * (
        1 if dates else 0 +
        1 if progress else 0 +
        1 if budget else 0 +
        1 if donations > 0 else 0 +
        1 if verified_donations > 0 else 0
    )


def get_level(status_by_category, score):
    desc = status_by_category.get('desc', False)
    progress = status_by_category.get('progress', False)
    budget = status_by_category.get('budget', False)

    if not desc or not progress or not budget:
        return 0
    if score < 40:
        return 1
    return 2


query = """
UPDATE map_action SET modified = %s::timestamptz, status_by_category = %s, score = %s, level = %s WHERE id = %s"""


@shared_task(name='sync_action_transparency')
def sync_action_transparency():
    with transaction.atomic():
        with connection.cursor() as cursor:
            for action in Action.objects.prefetch_related(
                Prefetch('testimonial_set', queryset=Testimonial.objects.filter(
                    published=True
                ), to_attr='testimonials'),
                Prefetch('donation_set', queryset=Donation.objects.filter(
                    approved_by_donor=True, approved_by_org=True
                ), to_attr='donations'),
                Prefetch('donation_set', queryset=Donation.objects.filter(
                    approved_by_donor=True, approved_by_org=True, donor__donoruser__isnull=False
                ).distinct(), to_attr='verified_donations'),
            ):
                status_by_category = {**action.status_by_category, **get_status_by_category(action, prefetched=True)}
                score = get_score(status_by_category)
                level = get_level(status_by_category, score)
                cursor.execute(query, [
                    timezone.now().isoformat(), json.dumps(status_by_category), score, level, action.id]
                )


@shared_task(name='sync_landing_page_data')
def sync_landing_page_data() -> Any:
    data_file_path = '/tmp/landing_data.json.gz'
    base_url = 'https://api.brigada.mx/api'

    paths = [
        ('metrics', '/landing_metrics/'),
        ('localities', '/localities_with_actions/'),
        ('opportunities', '/volunteer_opportunities_cached/?transparency_level__gte=2'),
        ('actions', '/actions_cached/?level__gte=2&fields=id,locality,organization,donations,action_type,target,unit_of_measurement'),
    ]
    data = {}

    for key, path in paths:
        r = requests.get(f'{base_url}{path}')
        raise_for_status(r)
        data[key] = r.json()

    with gzip.open(data_file_path, 'wb') as f:
        f.write(bytes(json.dumps(data), 'utf-8'))

    s3 = get_s3_client()
    with open(data_file_path, 'rb') as _data:
        s3.upload_fileobj(_data, 'brigada.mx', 'landing_data.json', ExtraArgs={
            'ACL': 'public-read',
            'CacheControl': 'max-age=86400',
            'ContentType': 'application/json',
            'ContentEncoding': 'gzip',
        })
