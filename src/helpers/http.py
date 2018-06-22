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


def raise_for_status(r):
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        try:
            json = r.json()
        except:
            pass
        else:
            raise requests.HTTPError(json) from e
        raise e


def download_file(url, dest, raise_exception=True):
    # https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
    r = requests.get(url, stream=True, allow_redirects=True, timeout=15)
    if r.status_code >= 400:
        if raise_exception:
            raise_for_status(r)
        return None
    with open(dest, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    return dest


def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv('CUSTOM_AWS_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('CUSTOM_AWS_SECRET_KEY'),
    )


def get_ses_client():
    return boto3.client(
        'ses',
        aws_access_key_id=os.getenv('CUSTOM_AWS_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('CUSTOM_AWS_SECRET_KEY'),
        region_name='us-west-2',
    )


def s3_thumbnail_url(url, width=0, height=0, crop=False):
    base_url = os.getenv('CUSTOM_THUMBOR_SERVER')
    path = urlparse(url).path
    return f'{base_url}/{"" if crop else "fit-in/"}{width}x{height}{path}'
