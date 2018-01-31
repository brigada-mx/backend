import os
import requests
from urllib.parse import urlparse

import boto3


class TokenAuth:
    def __init__(self, auth_prefix, token):
        self.auth_prefix = auth_prefix  # e.g. 'Bearer'
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = f'{self.auth_prefix} {self.token}'.strip()
        return r


def download_file(url, dest):
    r = requests.get(url, allow_redirects=True)
    if r.status_code >= 400:
        return None
    open(dest, 'wb').write(r.content)
    return dest


def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv('CUSTOM_AWS_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('CUSTOM_AWS_SECRET_KEY'),
    )


def s3_thumbnail_url(url, width=0, height=0, crop=False):
    base_url = os.getenv('CUSTOM_THUMBOR_SERVER')
    path = urlparse(url).path
    return f'{base_url}/{"" if crop else "fit-in/"}{width}x{height}{path}'
