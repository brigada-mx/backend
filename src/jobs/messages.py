from typing import List

from celery import shared_task

from helpers.http import get_ses_client


@shared_task(name='send_email', default_retry_delay=60, max_retries=3)
def send_email(
    to: List[str],
    subject: str,
    body: str,
    source: str = 'Brigada <contacto@brigada.mx>',
    reply_to: List[str] = None,
    **kwargs,
):
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
def send_personalized_email(to, subject, body, source='Brigada <contacto@brigada.mx>', reply_to=None, name=''):
    body = (f'Hola {name},<br><br>' if name else 'Hola,<br><br>') + body
    return send_email(to, subject, body, source, reply_to)


@shared_task(name='send_pretty_email', default_retry_delay=60, max_retries=3)
def send_pretty_email(to, subject, body, source='Eduardo Mancera <contacto@brigada.mx>', reply_to=None, name=''):
    body = (f'Hola {name},<br><br>' if name else 'Hola,<br><br>') + body
    body += """
    <br><br>
    Saludos,<br><br>
    Eduardo Mancera<br>
    Director de Brigada<br>
    <a href="mailto:contacto@brigada.mx">contacto@brigada.mx</a>
    """
    return send_email(to, subject, body, source, reply_to)
