import os
import random

from django.utils import timezone

from celery import shared_task

from db.map.models import EmailNotification, Organization, Donation
from db.users.models import DonorUser
from db.choices import ACTION_LABEL_BY_TYPE
from jobs.messages import send_email, send_pretty_email
from helpers.datetime import timediff


def organization_no_projects(n):
    organization = Organization.objects.get(id=n.args['organization_id'])
    actions = organization.action_set.filter(published=True)
    if len(actions) > 0:
        n.done = True
        n.save()
        return

    subject = 'Aún no has registrado un proyecto en Brigada'
    body = """Creaste tu cuenta de Brigada para {} hace {} días, pero todavía no has publicado ningún proyecto.<br><br>
    Crear y publicar un proyecto es fácil, <a href="{}/cuenta" target="_blank">entra a tu cuenta aquí</a> para hacerlo.<br><br>
    Si tienes cualquier problema, dale clic al botón de <b>Soporte</b> dentro de la plataforma. O, si no has hecho tu capacitación virtual, <a href="https://calendly.com/brigada/capacitacion" target="_blank">progámala aquí</a>.
    """.format(
        organization.name, round(timediff(timezone.now(), n.created, fmt='d')), os.getenv('CUSTOM_SITE_URL'))

    users = organization.organizationuser_set.all()
    return [{'to': [u.email], 'subject': subject, 'body': body, 'name': u.first_name} for u in users]


def organization_no_donations(n):
    organization = Organization.objects.prefetch_related('action_set__donation_set').get(id=n.args['organization_id'])
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
    Si tienes cualquier problema, te podemos ayudar desde el link de <b>Soporte</b>. O, si no has hecho tu capacitación virtual, <a href="https://calendly.com/brigada/capacitacion" target="_blank">progámala aquí</a>.
    """.format(
        len(actions), 's' if len(actions) > 1 else '', os.getenv('CUSTOM_SITE_URL'), action.key)

    users = organization.organizationuser_set.all()
    return [{'to': [u.email], 'subject': subject, 'body': body, 'name': u.first_name} for u in users]


def organization_no_photos(n):
    organization = Organization.objects.prefetch_related('action_set__submission_set').get(id=n.args['organization_id'])
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
    Si tienes cualquier problema, dale clic al link de <b>Soporte</b> dentro de la plataforma. O, si no has hecho tu capacitación virtual, <a href="https://calendly.com/brigada/capacitacion" target="_blank">progámala aquí</a>.
    """.format(
        len(actions), 's' if len(actions) > 1 else '')

    users = organization.organizationuser_set.all()
    return [{'to': [u.email], 'subject': subject, 'body': body, 'name': u.first_name} for u in users]


def donor_unclaimed(n=None, **kwargs):
    donation_id = n.args['donation_id'] if n else kwargs['donation_id']
    donation = Donation.objects.get(id=donation_id)

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
    action_label = ACTION_LABEL_BY_TYPE.get(action.action_type)

    subject = 'Encárgate de tu perfil en la plataforma Brigada'
    body = """En Brigada, {} ha dicho que donaste {}a su proyecto {}en {}.<br><br>
    Brigada es una red de {} organizaciones que en conjunto buscan reconstruir el país de manera transparente y eficiente.<br><br>
    Te invitamos a que <a href="{}" target="_blank">asumas control de tu perfil público</a> y verifiques la información correspondiente al donativo. De esta manera, puedes mostrar el impacto de tu apoyo y formar parte de nuestra comunidad.
    Si te interesa saber más sobre la plataforma, entra a <a href="http://brigada.mx" target="_blank">brigada.mx</a>.
    """.format(
        action.organization.name,
        '${:,.0f} MXN '.format(donation.amount) if donation.amount else '',
        f'de {action_label} ' if action_label else '',
        action.locality.name,
        Organization.objects.count() + DonorUser.objects.distinct('donor_id').count(),
        public_profile_url,
    )

    return [{'to': [email], 'subject': subject, 'body': body} for email in emails]


def donation_unapproved(n=None, **kwargs):
    donation_id = n.args['donation_id'] if n else kwargs['donation_id']
    notify = n.args['notify'] if n else kwargs['notify']
    created = n.args['created'] if n else kwargs['created']

    donation = Donation.objects.get(id=donation_id)
    if n and donation.approved_by_org and donation.approved_by_donor:
        n.done = True
        n.save()
        return

    if notify == 'org':
        name = donation.donor.name
        created_subject = f'Donador {name} te agregó un donativo'
        subject = created_subject if created else f'Donador {name} modificó uno de tus donativos'
        url = f"{os.getenv('CUSTOM_SITE_URL')}/cuenta/proyectos/{donation.action.key}"
        emails = list(donation.action.organization.organizationuser_set.values_list('email', flat=True))
    elif notify == 'donor':
        name = donation.action.organization.name
        created_subject = f'Reconstructor {name} te agregó un donativo'
        subject = created_subject if created else f'Reconstructor {name} modificó uno de tus donativos'
        url = f"{os.getenv('CUSTOM_SITE_URL')}/donador/donativos/{donation.id}"
        emails = list(donation.donor.donoruser_set.values_list('email', flat=True))

    body = """
    {} está esperando <a href="{}" target="_blank">a que lo apruebes aquí</a>. Si no lo abruebas, no aparece en tu perfil público, ni en el suyo.
    """.format(name, url)

    if donation.amount:
        body = f"El donativo tiene un valor de ${'{:,.0f}'.format(donation.amount)} MXN.<br><br>" + body

    return [{'to': [email], 'subject': subject, 'body': body} for email in emails]


notification_function_by_email_type = {
    'organization_no_projects': organization_no_projects,
    'organization_no_photos': organization_no_photos,
    'organization_no_donations': organization_no_donations,
    'donor_unclaimed': donor_unclaimed,
    'donation_unapproved': donation_unapproved,
}


def balance_schedule():
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
def send_email_notification(notification_id):
    n = EmailNotification.objects.get(id=notification_id)
    r_base = {'args': n.args, 'type': n.email_type}
    if not n.should_send() or not balance_schedule():
        return {**r_base, 'result': 'not_sent'}
    kwargs_sets = notification_function_by_email_type[n.email_type](n)
    if kwargs_sets is None:
        return {**r_base, 'result': 'not_sent'}
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
