import os
from concurrent import futures

from django.utils import timezone

from celery import shared_task

from db.map.models import Organization, EmailNotification
from jobs.messages import send_email_with_footer
from helpers.datetime import timediff


def organization_user_no_projects(n):
    organization = Organization.objects.get(id=n.args['organization_id'])
    actions = organization.action_set.filter(published=True)
    if len(actions) > 0:
        n.done = True
        n.save()
        return
    days = timediff(timezone.now(), n.created, fmt='d')
    if days < 3:
        return
    subject = 'Todavía no has publicado un proyecto en Brigada'
    body = """Creaste tu cuenta de Brigada para {} hace {} días, pero todavía no has publicado ningún proyecto.<br><br>
    <a href="{}/cuenta" target="_blank">Ve a tu cuenta aquí</a> para hacerlo.
    """.format(organization.name, round(days), os.getenv('CUSTOM_SITE_URL'))
    return send_email_with_footer(
        list(organization.organizationuser_set.values_list('email', flat=True)), subject, body)


def donation_unclaimed_donor(n):
    pass


notification_function_by_email_type = {
    'organization_user_no_projects': organization_user_no_projects,
    'donation_unclaimed_donor': donation_unclaimed_donor,
}


def send_email_notification(n):
    r_base = {'args': n.args, 'type': n.email_type}
    if not n.should_send():
        return {**r_base, 'result': 'not_sent'}
    try:
        res = notification_function_by_email_type[n.email_type](n)
    except Exception as e:
        return {**r_base, 'exception': str(e)}
    else:
        if res is None:
            return {**r_base, 'result': 'not_sent'}
        if res['ResponseMetadata']['HTTPStatusCode'] != 200:
            return {**r_base, 'error': res}
        n.increment_sent()
        return {**r_base, 'result': res}


@shared_task(name='send_email_notifications')
def send_email_notifications():
    MAX_WORKERS = 5
    notifications = EmailNotification.objects.filter(done=False)

    with futures.ThreadPoolExecutor(MAX_WORKERS) as executor:
        res = executor.map(send_email_notification, notifications)
    return [r for r in res if r]
