# https://kc.humanitarianresponse.info/edumancera/api-token
import os
import uuid
from concurrent import futures
from urllib.parse import quote_plus
from datetime import datetime, timedelta

from django.utils import timezone

from celery import shared_task
import requests

from db.map.models import Organization, Submission
from helpers.http import TokenAuth, download_file, get_s3_client
from helpers.location import geos_location_from_coordinates
from helpers.diceware import diceware_transform


AUTH_TOKEN = os.getenv('CUSTOM_KOBO_AUTH_TOKEN')
API_HOST = os.getenv('CUSTOM_KOBO_API_HOST')
TIMEOUT = 30


def get_form_ids():
    r = requests.get(API_HOST + '/data', auth=TokenAuth('Token', AUTH_TOKEN), timeout=TIMEOUT)
    r.raise_for_status()
    return [form['id'] for form in r.json()]


def get_recent_form_submissions(form_id, past_days=1):
    date = datetime.today() - timedelta(days=past_days)
    r = requests.get(
        API_HOST + '/data/{}'.format(form_id),
        params={'query': '{"_submission_time": {"$gte": "' + date.strftime('%Y-%m-%d') + '"}}'},
        auth=TokenAuth('Token', AUTH_TOKEN),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@shared_task(name='sync_submissions')
def sync_submissions(past_days=1):
    MAX_WORKERS = 10
    form_ids = get_form_ids()

    def sync_recent_form_submissions(form_id):
        submissions = get_recent_form_submissions(form_id, past_days)
        return [r for r in [sync_submission(s) for s in submissions] if r]

    with futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
        res = executor.map(sync_recent_form_submissions, form_ids)
    return [r for r in res if r]


def sync_submission(s):
    source_id = s['_id']
    if Submission.objects.filter(source='kobo', source_id=source_id).first():
        return

    organization = Organization.objects.filter(secret_key=diceware_transform(s.get('org_key'))).first()
    if organization is None:
        return
    action = organization.action_set.all().filter(key=int(s.get('action_key'))).first()
    submission = Submission(
        organization=organization,
        action=action,
        data=s,
        source='kobo',
        source_id=source_id,
        submitted=s['_submission_time'],
    )
    lat, lng = s['_geolocation']
    if lat and lng:
        submission.location = geos_location_from_coordinates(lat, lng)
    if '_attachments' in s:
        submission.image_urls = [a['download_url'] for a in (s.get('_attachments') or [])]
    submission.save()
    return repr(submission)


@shared_task(name='upload_submission_images')
def upload_submission_images(submission_id):
    submission = Submission.objects.get(id=submission_id)
    org_id = submission.organization_id
    s3 = get_s3_client()
    bucket = os.getenv('CUSTOM_AWS_STORAGE_BUCKET_NAME')

    urls = list(submission.image_urls)
    for i, url in enumerate(submission.image_urls):
        if url.startswith('https://{}.s3.amazonaws.com'.format(bucket)):
            continue
        filename = '{}-{}'.format(uuid.uuid4(), url.split('/')[-1].split('?')[0])
        path = download_file(url, os.path.join(os.sep, 'tmp', filename))
        if path is None:
            continue

        bucket_key = 'kobo/{}/{}'.format(org_id, filename)  # this will get URL encoded when it's uploaded to S3
        encoded_bucket_key = 'kobo/{}/{}'.format(org_id, quote_plus(filename))
        try:
            with open(path, 'rb') as data:
                s3.upload_fileobj(data, bucket, bucket_key, ExtraArgs={'ACL': 'public-read'})
        except:
            continue
        else:
            urls[i] = 'https://{}.s3.amazonaws.com/{}'.format(bucket, encoded_bucket_key)
    if urls != submission.image_urls:
        submission.image_urls = urls
        submission.save()


@shared_task(name='upload_recent_submission_images')
def upload_recent_submission_images(age_hours=1):
    for submission in Submission.objects.filter(submitted__gte=timezone.now() - timedelta(hours=age_hours)):
        try:
            upload_submission_images(submission.id)
        except Submission.DoesNotExist:
            continue
