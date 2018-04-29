from celery import shared_task

from helpers.http import get_ses_client


@shared_task(name='send_email', default_retry_delay=60, max_retries=3)
def send_email(to, subject, body, source='Brigada <accounts@brigada.mx>', reply_to=None, **kwargs):
    return get_ses_client().send_email(
        Source=source,
        Destination={
            'ToAddresses': to,
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


@shared_task(name='send_pretty_email', default_retry_delay=60, max_retries=3)
def send_pretty_email(to, subject, body, source='Eduardo Mancera <eduardo@brigada.mx>', reply_to=None, name=''):
    body = (f'Hola {name},<br><br>' if name else 'Hola,<br><br>') + body
    body += """
    <br><br>
    Saludos,<br><br>
    Eduardo Mancera<br>
    Director de Brigada<br>
    <a href="mailto:eduardo@brigada.mx">eduardo@brigada.mx</a>
    """
    return send_email(to, subject, body, source, reply_to)
