from typing import Dict, Callable
import os
import random

from django.utils import timezone

from celery import shared_task
from raven.contrib.django.raven_compat.models import client

from db.map.models import EmailNotification, Organization, Donation, VolunteerApplication
from db.users.models import DonorUser
from jobs.messages import send_email, send_pretty_email, send_personalized_email
from helpers.datetime import timediff


@shared_task(name='send_volunteer_application_email')
def send_volunteer_application_email(application_id):
    application = VolunteerApplication.objects.get(id=application_id)
    action = application.opportunity.action
    locality_label = f'{action.locality.name}, {action.locality.state_name}'

    subject = '{} quiere ser voluntario para tu proyecto de {} en {}'.format(
        application.user.full_name, action.action_label() or '-', locality_label,
    )
    body = """{} quiere ser voluntario para tu proyecto de {} en {}. Aplicó para el puesto de {}.<br><br>
    Aquí están sus datos de contacto:<br>
    Teléfono: {}<br>
    Email: {}<br><br>
    Le gustaría trabajar con ustedes porque: <b>{}</b><br><br>
    Por favor mándale una respuesta. Si esta oportunidad ya no está disponible, <a href="{}/cuenta/proyectos/{}" target="_blank">actualízala aquí</a>.
    """.format(
        application.user.full_name, action.action_label() or '-', locality_label, application.opportunity.position,
        application.user.phone, application.user.email, application.reason_why,
        os.getenv('CUSTOM_SITE_URL'), action.key,
    )

    users = action.organization.organizationuser_set.all()
    for u in users:
        send_personalized_email.delay(to=[u.email], subject=subject, body=body, name=u.first_name)


def organization_no_projects(n):
    try:
        organization = Organization.objects.get(id=n.args['organization_id'])
    except Organization.DoesNotExist:
        client.captureException(None, level='warning')
        return

    actions = organization.action_set.filter(published=True)
    if len(actions) > 0:
        n.done = True
        n.save()
        return

    subject = 'Aún no has registrado un proyecto en Brigada'
    body = """Creaste tu cuenta de Brigada para {} hace {} días, pero todavía no has publicado ningún proyecto.<br><br>
    Crear y publicar un proyecto es fácil, <a href="{}/cuenta" target="_blank">entra a tu cuenta aquí</a> para hacerlo.<br><br>
    Si tienes cualquier problema, dale clic al botón de <b>Soporte</b> dentro de la plataforma. O, si no has hecho tu capacitación virtual, <a href="mailto:eduardo@brigada.mx?Subject=Brigada Agendar Capacitación" target="_blank">progámala aquí</a>.
    """.format(
        organization.name, round(timediff(timezone.now(), n.created, fmt='d')), os.getenv('CUSTOM_SITE_URL'))

    users = organization.organizationuser_set.all()
    return [{'to': [u.email], 'subject': subject, 'body': body, 'name': u.first_name} for u in users]


def organization_no_donations(n):
    try:
        organization = Organization.objects.prefetch_related(
            'action_set__donation_set'
        ).get(id=n.args['organization_id'])
    except Organization.DoesNotExist:
        client.captureException(None, level='warning')
        return

    actions = organization.action_set.all()
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

    subject = 'En Brigada queremos presumir a tus donadores'
    body = """Ya creaste {} proyecto{} en tu cuenta de Brigada, pero no has registrado ningún donativo.<br><br>
    Al registrar tus donativos, le darás mayor legitimidad de tus proyectos ante la comunidad de Brigada.<br><br>
    Hacerlo es fácil. <a href="{}/cuenta/proyectos/{}" target="_blank">Entra a tu cuenta</a>, abre uno de tus proyectos y dale clic al botón <b>Agregar</b> en la sección de <b>Donativos</b>.<br><br>
    Si tienes cualquier problema, te podemos ayudar desde el link de <b>Soporte</b>. O, si no has hecho tu capacitación virtual, <a href="mailto:eduardo@brigada.mx?Subject=Brigada Agendar Capacitación" target="_blank">progámala aquí</a>.
    """.format(
        len(actions), 's' if len(actions) > 1 else '', os.getenv('CUSTOM_SITE_URL'), action.key)

    users = organization.organizationuser_set.all()
    return [{'to': [u.email], 'subject': subject, 'body': body, 'name': u.first_name} for u in users]


def organization_no_photos(n):
    try:
        organization = Organization.objects.prefetch_related(
            'action_set__submission_set'
        ).get(id=n.args['organization_id'])
    except Organization.DoesNotExist:
        client.captureException(None, level='warning')
        return

    actions = organization.action_set.all()
    action = actions.first()
    if action is None:
        return

    days = timediff(timezone.now(), action.created, fmt='d')
    if days < 4:
        return

    for action in actions:
        for submission in action.submission_set.all():
            n.done = True
            n.save()
            return

    subject = 'Sube fotos de tus proyectos en Brigada'
    body = """Ya creaste {} proyecto{} en tu cuenta de Brigada, pero no has compartido fotos con nuestra comunidad. Las organizacaiones que agregan fotos a sus proyectos reciben 3 veces más visitas a su perfil.<br><br>
    Agregar fotos a un proyecto es fácil, <a href="http://fotos.brigada.mx/subir" target="_blank">llena este formulario</a> para hacerlo.<br><br>
    Si tienes cualquier problema, dale clic al link de <b>Soporte</b> dentro de la plataforma. O, si no has hecho tu capacitación virtual, <a href="mailto:eduardo@brigada.mx?Subject=Brigada Agendar Capacitación" target="_blank">progámala aquí</a>.
    """.format(
        len(actions), 's' if len(actions) > 1 else '')

    users = organization.organizationuser_set.all()
    return [{'to': [u.email], 'subject': subject, 'body': body, 'name': u.first_name} for u in users]


def donor_unclaimed(n=None, **kwargs):
    donation_id = n.args['donation_id'] if n else kwargs['donation_id']
    try:
        donation = Donation.objects.get(id=donation_id)
    except Donation.DoesNotExist:
        client.captureException(None, level='warning')
        return

    donor = donation.donor
    action = donation.action
    if n and len(donor.donoruser_set.all()) > 0:
        n.done = True
        n.save()
        return

    try:
        emails = donor.contact['contact_emails']
    except:
        return []

    public_profile_url = f"{os.getenv('CUSTOM_SITE_URL')}/donadores/{donor.id}"
    action_label = action.action_label()

    subject = 'Encárgate de tu perfil en la plataforma Brigada'
    body = """En Brigada, {} ha dicho que donaste {}a su proyecto {}en {}.<br><br>
    Brigada es una red de {} organizaciones que en conjunto buscan reconstruir el país de manera transparente y eficiente.<br><br>
    Te invitamos a que <a href="{}" target="_blank">asumas control de tu perfil público</a> y verifiques la información correspondiente al donativo. De esta manera, puedes mostrar el impacto de tu apoyo y formar parte de nuestra comunidad.
    Si te interesa saber más sobre la plataforma, entra a <a href="http://brigada.mx" target="_blank">brigada.mx</a>.
    """.format(
        action.organization.name,
        '${:,.0f} MXN '.format(donation.amount) if donation.amount else '',
        f'de <b>{action_label}</b> ' if action_label else '',
        f'<b>{action.locality.name}, {action.locality.state_name}</b>',
        Organization.objects.count() + DonorUser.objects.distinct('donor_id').count(),
        public_profile_url,
    )

    return [{'to': [email], 'subject': subject, 'body': body} for email in emails]


def donation_unapproved(n=None, **kwargs):
    donation_id = n.args['donation_id'] if n else kwargs['donation_id']
    notify = n.args['notify'] if n else kwargs['notify']
    # we also have a 'created' arg we might want to use

    try:
        donation = Donation.objects.get(id=donation_id)
    except Donation.DoesNotExist:
        client.captureException(None, level='warning')
        return

    if n and donation.approved_by_org and donation.approved_by_donor:
        n.done = True
        n.save()
        return

    action = donation.action
    action_label = action.action_label()

    if notify == 'org':
        name = donation.donor.name
        subject = f'{name} espera tu aprobación'
        url = f"{os.getenv('CUSTOM_SITE_URL')}/cuenta/proyectos/{donation.action.key}"
        emails = list(action.organization.organizationuser_set.values_list('email', flat=True))
    elif notify == 'donor':
        name = action.organization.name
        subject = f'{name} espera tu aprobación'
        url = f"{os.getenv('CUSTOM_SITE_URL')}/donador/donativos/{donation.id}"
        emails = list(donation.donor.donoruser_set.values_list('email', flat=True))

    body = """{} está esperando a que apruebes su donativo {}{}en {}. <a href="{}" target="_blank">Da clic aquí para revisarlo.</a><br><br>

    Si no lo abruebas, no aparece en tu perfil público, ni en el suyo.
    """.format(
        name,
        'de ${:,.0f} MXN '.format(donation.amount) if donation.amount else '',
        f'para <b>{action_label}</b> ' if action_label else '',
        f'<b>{action.locality.name}, {action.locality.state_name}</b>',
        url,
    )

    return [{'to': [email], 'subject': subject, 'body': body} for email in emails]


notification_function_by_email_type: Dict[str, Callable] = {
    'organization_no_projects': organization_no_projects,
    'organization_no_photos': organization_no_photos,
    'organization_no_donations': organization_no_donations,
    'donor_unclaimed': donor_unclaimed,
    'donation_unapproved': donation_unapproved,
}


def balance_schedule() -> bool:
    weekday = timezone.now().isoweekday()
    r = random.random()
    if weekday == 1:
        return r <= 0.25
    if weekday == 2:
        return r <= 0.25
    if weekday == 3:
        return r <= 0.5
    return True


@shared_task(name='send_email_notification')
def send_email_notification(notification_id) -> Dict:
    n = EmailNotification.objects.get(id=notification_id)
    r_base = {'args': n.args, 'type': n.email_type}
    if not balance_schedule():
        return {**r_base, 'result': 'balance_schedule_not_sent'}
    if not n.should_send():
        return {**r_base, 'result': 'should_send_not_sent'}
    kwargs_sets = notification_function_by_email_type[n.email_type](n)
    if kwargs_sets is None:
        return {**r_base, 'result': 'notification_function_not_sent'}
    for kwargs_set in kwargs_sets:
        if n.pretty:
            send_pretty_email.delay(**kwargs_set)
        else:
            send_email.delay(**kwargs_set)
    n.increment_sent()
    return {**r_base, 'result': kwargs_sets}


@shared_task(name='send_email_notifications')
def send_email_notifications():
    notifications = EmailNotification.objects.filter(done=False)
    for n in notifications:
        send_email_notification.delay(n.id)
