from typing import Dict, Any
import json
import gzip

from django.db.models import Prefetch
from django.db import transaction, connection
from django.utils import timezone

from celery import shared_task
import requests

from helpers.http import get_s3_client, raise_for_status
from db.map.models import Action, Donation, Testimonial


def get_status_by_category(action, prefetched=False) -> Dict[str, Any]:
    d: Dict[str, Any] = {}

    d['desc'] = bool(action.desc)

    d['dates'] = bool(action.start_date and action.end_date)

    d['progress'] = bool(action.unit_of_measurement) and action.target is not None

    d['budget'] = bool(action.budget)

    if action.beneficiaries_criteria == 'other':
        d['beneficiaries'] = bool(action.beneficiaries_desc and action.beneficiaries_criteria_desc)
    else:
        d['beneficiaries'] = bool(action.beneficiaries_desc and action.beneficiaries_criteria)

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


def get_score(status_by_category: Dict[str, Any]) -> float:
    dates = status_by_category.get('dates', False)
    progress = status_by_category.get('progress', False)
    budget = status_by_category.get('budget', False)
    beneficiaries = status_by_category.get('beneficiaries', False)
    image_count = status_by_category.get('image_count', 0)
    testimonials = status_by_category.get('testimonials', 0)
    donations = status_by_category.get('donations', 0)
    verified_donations = status_by_category.get('verified_donations', 0)

    return (image_count + testimonials * 5) * (
        (1 if dates else 0) +
        (1 if progress else 0) +
        (1 if budget else 0) +
        (1 if beneficiaries else 0) +
        (1 if donations > 0 else 0) +
        (1 if verified_donations > 0 else 0)
    )


def get_level(status_by_category: Dict[str, Any]) -> int:
    desc = status_by_category.get('desc', False)
    dates = status_by_category.get('dates', False)
    progress = status_by_category.get('progress', False)
    budget = status_by_category.get('budget', False)
    beneficiaries = status_by_category.get('beneficiaries', False)
    image_count = status_by_category.get('image_count', 0)
    testimonials = status_by_category.get('testimonials', 0)

    if not desc or not progress or not budget:
        return 0
    if image_count < 10 and testimonials < 2:
        return 1
    if not beneficiaries or not dates:
        return 2
    return 3


query = """
UPDATE map_action SET modified = %s::timestamptz, status_by_category = %s, score = %s, level = %s WHERE id = %s"""


@shared_task(name='sync_action_transparency')
def sync_action_transparency() -> None:
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
                level = get_level(status_by_category)
                cursor.execute(query, [
                    timezone.now().isoformat(), json.dumps(status_by_category), score, level, action.id]
                )


@shared_task(name='sync_landing_page_data', default_retry_delay=30, max_retries=3)
def sync_landing_page_data() -> None:
    data_file_path = '/tmp/landing_data.json.gz'
    r = requests.get('https://api.brigada.mx/api/landing/')
    raise_for_status(r)

    with gzip.open(data_file_path, 'wb') as f:
        f.write(bytes(json.dumps(r.json()), 'utf-8'))

    s3 = get_s3_client()
    with open(data_file_path, 'rb') as data:
        s3.upload_fileobj(data, 'brigada.mx', 'landing_data.json', ExtraArgs={
            'ACL': 'public-read',
            'CacheControl': 'max-age=43200',
            'ContentType': 'application/json',
            'ContentEncoding': 'gzip',
        })
