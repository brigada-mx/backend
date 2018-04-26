import os
from concurrent import futures

from django.utils import timezone

from celery import shared_task

from db.map.models import EmailNotification, Organization, Action
from jobs.messages import send_email_with_footer
from helpers.datetime import timediff


def organization_no_projects(n):
    organization = Organization.objects.get(id=n.args['organization_id'])
    actions = organization.action_set.filter(published=True)
    if len(actions) > 0:
        n.done = True
        n.save()
        return

    subject = 'Todavía no has publicado un proyecto en Brigada'
    body = """Creaste tu cuenta de Brigada para {} hace {} días, pero todavía no has publicado ningún proyecto.<br><br>
    Crear y publicar un proyecto es fácil, <a href="{}/cuenta" target="_blank">ve a tu cuenta aquí</a> para hacerlo.<br><br>
    Si tienes cualquier problema, dale clic al botón de <b>Soporte</b> dentro de la plataforma. O, si no has hecho tu capacitación virtual, <a href="https://calendly.com/brigada/capacitacion" target="_blank">progámala aquí</a>.
    """.format(
        organization.name, round(timediff(timezone.now(), n.created, fmt='d')), os.getenv('CUSTOM_SITE_URL'))

    return send_email_with_footer(
        list(organization.organizationuser_set.values_list('email', flat=True)), subject, body)


def organization_no_donations(n):
    organization = Organization.objects.prefetch_related('action_set__donation_set').get(id=n.args['organization_id'])
    actions = organization.action_set.all().order_by('created')
    action = actions.first()
    if action is None:
        return

    days = timediff(timezone.now(), action.created, fmt='d')
    if days < 3:
        return

    for action in actions:
        for donation in action.donation_set.all():
            n.done = True
            n.save()
            return

    subject = '¿Cómo se están financiando tus proyectos en Brigada?'
    body = """Ya creaste {} proyecto{} en tu cuenta de Brigada, pero no has agregado ningún donativo.<br><br>
    Agregar un donativo a un proyecto es fácil, <a href="{}/cuenta/proyectos/{}" target="_blank">ve a tu cuenta aquí</a> para hacerlo.<br><br>
    Si tienes cualquier problema, dale clic al botón de <b>Soporte</b> dentro de la plataforma. O, si no has hecho tu capacitación virtual, <a href="https://calendly.com/brigada/capacitacion" target="_blank">progámala aquí</a>.
    """.format(
        len(actions), 's' if len(actions) > 1 else '', os.getenv('CUSTOM_SITE_URL'), action.key)

    return send_email_with_footer(
        list(organization.organizationuser_set.values_list('email', flat=True)), subject, body)


def organization_no_photos(n):
    organization = Organization.objects.prefetch_related('action_set__submission_set').get(id=n.args['organization_id'])
    actions = organization.action_set.all().order_by('created')
    action = actions.first()
    if action is None:
        return

    days = timediff(timezone.now(), action.created, fmt='d')
    if days < 3:
        return

    for action in actions:
        for subsmission in action.subsmission_set.all():
            n.done = True
            n.save()
            return

    subject = '¡Documenta tus proyectos con fotos en Brigada!'
    body = """Ya creaste {} proyecto{} en tu cuenta de Brigada, pero no los has documentado con fotos. Organizacaiones que agregan fotos a sus proyectos reciben 3 veces más visitas que los que no lo hacen.<br><br>
    Agregar fotos a un proyecto es fácil, <a href="http://fotos.brigada.mx/subir" target="_blank">llena este formulario</a> para hacerlo.<br><br>
    Si tienes cualquier problema, dale clic al botón de <b>Soporte</b> dentro de la plataforma. O, si no has hecho tu capacitación virtual, <a href="https://calendly.com/brigada/capacitacion" target="_blank">progámala aquí</a>.
    """.format(
        len(actions), 's' if len(actions) > 1 else '')

    return send_email_with_footer(
        list(organization.organizationuser_set.values_list('email', flat=True)), subject, body)


def donation_unclaimed_donor(n):
    pass


def unapproved_donation(n):
    pass


notification_function_by_email_type = {
    'organization_no_projects': organization_no_projects,
    'organization_no_photos': organization_no_photos,
    'organization_no_donations': organization_no_donations,
    'donation_unclaimed_donor': donation_unclaimed_donor,
    'unapproved_donation': unapproved_donation,
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
