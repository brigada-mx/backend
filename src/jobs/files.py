import os
from concurrent import futures
from datetime import timedelta

from django.utils import timezone

import piexif
from celery import shared_task
from raven.contrib.django.raven_compat.models import client

from db.map.models import Submission
from helpers.http import download_file
from helpers import get_image_size


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
