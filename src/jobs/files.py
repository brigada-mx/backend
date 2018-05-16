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
    return in_s3 and image.get('exif') is not None


def in_s3(url):
    bucket = os.getenv('CUSTOM_AWS_STORAGE_BUCKET_NAME')
    return url.startswith(f'https://{bucket}.s3.amazonaws.com')


def exif_data(image_path):
    try:
        data = piexif.load(image_path)
        return str(data)
    except:
        client.captureException()
        return str(None)


@shared_task(name='sync_submissions_meta')
def sync_submissions_meta(past_days=None):
    if past_days is None:
        submissions = Submission.objects.all()
    else:
        submissions = Submission.objects.filter(created__gt=timezone.now() - timedelta(days=past_days))

    for s in submissions:
        if all(image_meta_synced(i) for i in s.image_urls):
            continue
        sync_submission_meta.delay(s.submission_id)


@shared_task(name='sync_submission_meta')
def sync_submission_meta(submission_id):
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
        except get_image_size.UnknownImageFormat:
            width, height, extension = None, None, None

        image['exif'] = exif_data(path)  # pass this string to `ast.literal_eval` to recover exif dict
        image['width'] = width
        image['height'] = height
        image['extension'] = extension
        return image

    with futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
        res = executor.map(get_image_meta, submission.image_urls)
    submission.image_urls = [i for i in res]

    submission.save()
