# https://kc.humanitarianresponse.info/edumancera/api-token
import os
from concurrent import futures
from datetime import datetime, timedelta

import requests

from db.map.models import Organization, Submission
from helpers.http import TokenAuth
from helpers.location import geos_location_from_coordinates


AUTH_TOKEN = os.getenv('CUSTOM_KOBO_AUTH_TOKEN')
API_HOST = os.getenv('CUSTOM_KOBO_API_HOST')
TIMEOUT = 30


class KoboException(Exception):
    pass


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
    if r.status >= 400:
        return []
    return r.json()


def sync_submissions():
    MAX_WORKERS = 10
    form_ids = get_form_ids()

    def sync_recent_form_submissions(form_id):
        submissions = get_recent_form_submissions(form_id)
        for s in submissions:
            sync_submission(s)

    with futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
        res = executor.map(sync_recent_form_submissions, form_ids)
    return res


def sync_submission(s):
    source_id = s['_id']
    if Submission.objects.filter(source='kobo', source_id=source_id).first():
        return

    organization = Organization.objects.filter(uuid=s['org_id']).first()
    if organization is None:
        return
    action = organization.action_set.all().filter(key=int(s['action_id'])).first()

    Submission.objects.create(
        location=geos_location_from_coordinates(*s['_geolocation']),
        organization=organization,
        action=action,
        data=s,
        source='kobo',
        source_id=source_id,
        submitted=s['_submission_time'],
    )
