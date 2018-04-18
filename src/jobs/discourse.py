import os
from concurrent import futures

import requests
from celery import shared_task


API_HOST = os.getenv('CUSTOM_DISCOURSE_API_HOST')
API_KEY = os.getenv('CUSTOM_DISCOURSE_API_KEY')
AUTH_PARAMS = {'api_key': API_KEY, 'api_username': 'system'}
TIMEOUT = 30


def get_user_ids(exclude_emails=None):
    r = requests.get(API_HOST + '/admin/users.json', params={**AUTH_PARAMS, **{'show_emails': 'true'}}, timeout=TIMEOUT)
    r.raise_for_status()
    exclude_emails = exclude_emails or []
    return [user['id'] for user in r.json() if user['email'] not in exclude_emails]


@shared_task(name='discourse_log_out_users')
def discourse_log_out_users():
    from django.conf import settings
    if not settings.ENVIRONMENT == 'production':
        return

    MAX_WORKERS = 10
    user_ids = get_user_ids([
        'kylebebak@gmail.com', 'eduardo@fortana.co', 'support+hostedsite@discourse.org', 'discobot_email', 'no_email'])

    def log_out_user(user_id):
        r = requests.post(API_HOST + f'/admin/users/{user_id}/log_out', params=AUTH_PARAMS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()

    with futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
        res = executor.map(log_out_user, user_ids)
    return [r for r in res if r]
