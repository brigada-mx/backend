from celery import shared_task

from helpers.http import get_ses_client


@shared_task(name='notify', default_retry_delay=30, max_retries=3)
def send_email(recipients, subject, body, source='accounts@brigada.mx', reply_to=None):
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
