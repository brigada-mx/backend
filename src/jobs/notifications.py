from concurrent import futures

from celery import shared_task

from db.map.models import EmailNotification
from jobs.messages import send_email_with_footer


function_by_email_type = {}


@shared_task(name='send_email_notifications')
def send_email_notifications():
    MAX_WORKERS = 5
    notifications = EmailNotification.objects.filter(done=False)

    def send_notification(n):
        r_base = {'email': n.email, 'type': n.email_type}
        if not n.should_send():
            return {**r_base, 'result': 'not_sent'}
        try:
            res = function_by_email_type[n.email_type](n)
        except Exception as e:
            return {**r_base, 'exception': str(e)}
        else:
            if res['ResponseMetadata']['HTTPStatusCode'] != 200:
                return {**r_base, 'error': res}
            n.increment_sent()
            return {**r_base, 'result': res}

    with futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
        res = executor.map(send_notification, notifications)
    return [r for r in res if r]
