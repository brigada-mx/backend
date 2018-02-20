import os

import boto3


def get_ses_client():
    return boto3.client(
        'ses',
        aws_access_key_id=os.getenv('CUSTOM_AWS_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('CUSTOM_AWS_SECRET_KEY'),
        region_name='us-west-2',
    )


def send_email(recipients, subject, body, source='accounts@ensintonia.org', reply_to=None):
    return get_ses_client().send_email(
        Source=source,
        Destination={
            'ToAddresses': recipients,
        },
        Message={
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8',
            },
            'Body': {
                'Html': {
                    'Data': body,
                    'Charset': 'UTF-8',
                }
            }
        },
        ReplyToAddresses=reply_to or [],
    )
