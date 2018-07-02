# https://kc.humanitarianresponse.info/edumancera/api-token
import os
import uuid
from concurrent import futures
from datetime import datetime, timedelta

from django.utils import timezone

from celery import shared_task
import requests

from db.map.models import Organization, Submission
from helpers.http import TokenAuth, download_file, get_s3_client, s3_safe_filename, raise_for_status
from helpers.location import geos_location_from_coordinates
from helpers.diceware import diceware_transform


AUTH_TOKEN = os.getenv('CUSTOM_KOBO_AUTH_TOKEN')
API_HOST = os.getenv('CUSTOM_KOBO_API_HOST')
TIMEOUT = 30


def get_form_ids():
    r = requests.get(API_HOST + '/data', auth=TokenAuth('Token', AUTH_TOKEN), timeout=TIMEOUT)
    raise_for_status(r)
    return [form['id'] for form in r.json()]


def get_recent_form_submissions(form_id, past_days=1):
    date = datetime.today() - timedelta(days=past_days)
    r = requests.get(
        API_HOST + f'/data/{form_id}',
        params={'query': '{"_submission_time": {"$gte": "' + date.strftime('%Y-%m-%d') + '"}}'},
        auth=TokenAuth('Token', AUTH_TOKEN),
        timeout=TIMEOUT,
    )
    raise_for_status(r)
    return r.json()


@shared_task(name='sync_submissions')
def sync_submissions(past_days=1):
    MAX_WORKERS = 10
    form_ids = get_form_ids()

    def sync_recent_form_submissions(form_id):
        try:
            submissions = get_recent_form_submissions(form_id, past_days)
        except requests.exceptions.RequestException as e:
            return {'exception': str(e)}
        return [r for r in [sync_submission(s) for s in submissions] if r]

    with futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
        res = executor.map(sync_recent_form_submissions, form_ids)
    return [r for r in res if r]


def sync_submission(s):
    source_id = s['_id']
    if Submission.objects.filter(source='kobo', source_id=source_id).first():
        return

    organization = Organization.objects.filter(secret_key=diceware_transform(s.get('org_key'))).first()
    action = organization and organization.action_set.all().filter(key=int(s.get('action_key'))).first()
    submission = Submission(
        organization=organization,
        action=action,
        data=s,
        source='kobo',
        source_id=source_id,
        submitted=s.get('end') or s['_submission_time'] or '',
    )
    lat, lng = s['_geolocation']
    if lat and lng:
        submission.location = geos_location_from_coordinates(lat, lng)
    if '_attachments' in s:
        submission.images = [{'url': a['download_url']} for a in (s.get('_attachments') or [])]
    submission.save()
    return repr(submission)


@shared_task(name='upload_submission_images')
def upload_submission_images(submission_id):
    from jobs.files import sync_submission_image_meta
    from django.conf import settings
    if not settings.ENVIRONMENT == 'production':
        return

    submission = Submission.objects.get(id=submission_id)
    org_id = submission.organization_id
    if org_id is None:
        org_id = 'null'
    s3 = get_s3_client()
    bucket = os.getenv('CUSTOM_AWS_STORAGE_BUCKET_NAME')

    save = False
    for i, image in enumerate(submission.images):
        url = image['url']
        if url.startswith(f'https://{bucket}.s3.amazonaws.com'):
            continue
        save = True
        filename = s3_safe_filename(f'{uuid.uuid4()}-{url.split("/")[-1].split("?")[0]}')
        path = download_file(url, os.path.join(os.sep, 'tmp', filename), raise_exception=False)
        if path is None:
            continue

        bucket_key = f'kobo/{org_id}/{filename}'

        try:
            with open(path, 'rb') as data:
                s3.upload_fileobj(data, bucket, bucket_key, ExtraArgs={'ACL': 'public-read'})
        except:
            continue
        else:
            submission.images[i] = {'url': f'https://{bucket}.s3.amazonaws.com/{bucket_key}'}
    if save:
        submission.save()
        sync_submission_image_meta.delay(submission.id)


@shared_task(name='upload_recent_submission_images')
def upload_recent_submission_images(age_hours=1):
    for submission in Submission.objects.filter(submitted__gte=timezone.now() - timedelta(hours=age_hours)):
        try:
            upload_submission_images(submission.id)
        except Submission.DoesNotExist:
            continue
