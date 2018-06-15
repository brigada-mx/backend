import os
from concurrent import futures
from datetime import timedelta

from django.utils import timezone
from django.db import transaction

import piexif
import requests
from celery import shared_task
from raven.contrib.django.raven_compat.models import client

from db.map.models import Submission, Testimonial, YoutubeAccessToken
from helpers.http import download_file
from helpers import get_image_size


def video_meta_synced(video):
    return 'youtube_video_id' in video


def image_meta_synced(image):
    return 'exif' in image


def in_s3(url):
    bucket = os.getenv('CUSTOM_AWS_STORAGE_BUCKET_NAME')
    return url.startswith(f'https://{bucket}.s3.amazonaws.com')


def exif_data(image_path):
    try:
        data = piexif.load(image_path)
    except:
        client.captureException()
        return str(None)
    else:
        try:
            del data['thumbnail']
        except:
            pass
        return str(data)


@shared_task(name='sync_submissions_image_meta')
def sync_submissions_image_meta(past_hours=None):
    if past_hours is None:
        submissions = Submission.objects.all()
    else:
        submissions = Submission.objects.filter(created__gt=timezone.now() - timedelta(hours=past_hours))

    for s in submissions:
        if all(image_meta_synced(i) or not in_s3(i['url']) for i in s.images):
            continue
        sync_submission_image_meta.delay(s.id)


@shared_task(name='sync_submission_image_meta')
def sync_submission_image_meta(submission_id):
    MAX_WORKERS = 10
    submission = Submission.objects.get(id=submission_id)

    def get_image_meta(image):
        if image_meta_synced(image) or not in_s3(image['url']):
            return image

        url = image['url']
        path = download_file(url, os.path.join(os.sep, 'tmp', url.split('/')[-1]))
        if path is None:
            return image

        try:
            meta = get_image_size.get_image_metadata(path)
            width, height, extension = meta.width, meta.height, meta.type
        except:
            client.captureException()
            width, height, extension = None, None, None

        image['exif'] = exif_data(path)  # pass this string to `ast.literal_eval` to recover exif dict
        image['width'] = width
        image['height'] = height
        image['extension'] = extension
        return image

    with futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
        res = executor.map(get_image_meta, submission.images)
    submission.images = [i for i in res]

    submission.save()


@shared_task(name='sync_testimonial_video_meta', default_retry_delay=30, max_retries=3)
def sync_testimonial_video_meta(testimonial_id):
    # supported file formats: https://support.google.com/youtube/troubleshooter/2888402?hl=en
    testimonial = Testimonial.objects.get(id=testimonial_id)

    def update_video_meta(t):
        if video_meta_synced(t.video):
            return

        url = t.video['url']
        path = download_file(url, os.path.join(os.sep, 'tmp', url.split('/')[-1]))
        if path is None:
            return

        name = t.recipient.get('first_name')
        name_part = f'de {name} ' if name else ''
        locality = t.action.locality
        meta = {
            'snippet': {
                'categoryId': '29',  # nonprofits and activism
                'description': f'Este es un proyecto de {t.action.action_label()} en {locality.name}, {locality.state_name}, realizado por {t.action.organization.name}.\n\n{os.getenv("CUSTOM_SITE_URL")}/proyectos/{t.action.id}',
                'title': f'Testimonio {name_part}en {locality.name}',
            },
            'status': {'privacyStatus': 'public'},
        }
        params = {'part': 'snippet,status', 'uploadType': 'resumable'}

        token = YoutubeAccessToken.objects.get(token_type='Bearer')
        headers = {'Authorization': 'Bearer {}'.format(token.access_token)}

        r = requests.post('https://www.googleapis.com/upload/youtube/v3/videos',
                          json=meta, headers=headers, params=params)
        r.raise_for_status()

        if t.video.get('in_flight'):
            return
        t.video['in_flight'] = True
        t.save()

        with open(path, 'rb') as data:
            r = requests.post(r.headers['location'], headers=headers, data=data)
            r.raise_for_status()

        data = r.json()
        t.video['youtube_response_data'] = data
        t.video['youtube_video_id'] = data['id']
        try:
            t.video['url_thumbnail'] = data['snippet']['thumbnails']['high']['url']
        except:
            pass
        t.video['in_flight'] = False
        t.save()

    with transaction.atomic():
        update_video_meta(testimonial)


@shared_task(name='sync_testimonials_video_meta')
def sync_testimonials_video_meta(past_hours=None):
    if past_hours is None:
        testimonials = Testimonial.objects.all()
    else:
        testimonials = Testimonial.objects.filter(created__gt=timezone.now() - timedelta(hours=past_hours))

    for t in testimonials:
        if video_meta_synced(t.video):
            continue
        sync_testimonial_video_meta.delay(t.id)


@shared_task(name='refresh_youtube_access_token', default_retry_delay=30, max_retries=3)
def refresh_youtube_access_token():
    r = requests.post(
        'https://www.googleapis.com/oauth2/v4/token',
        data={
            'client_id': os.getenv('CUSTOM_GOOGLE_OAUTH_CLIENT_ID'),
            'client_secret': os.getenv('CUSTOM_GOOGLE_OAUTH_CLIENT_SECRET'),
            'refresh_token': os.getenv('CUSTOM_GOOGLE_OAUTH_REFRESH_TOKEN'),
            'grant_type': 'refresh_token'
        }
    )
    r.raise_for_status()
    data = r.json()

    try:
        token = YoutubeAccessToken.objects.get(token_type='Bearer')
    except YoutubeAccessToken.DoesNotExist:
        token = YoutubeAccessToken()
    token.access_token = data['access_token']
    token.expires_in = data['expires_in']
    token.token_type = 'Bearer'
    token.save()
