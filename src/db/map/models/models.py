import os

from django.contrib.gis.db import models
from django.db import transaction
from django.db.models import Max
from django.db.utils import IntegrityError
from django.utils import timezone
from django.contrib.postgres.fields import JSONField, ArrayField
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from db.config import BaseModel
from db.choices import SCIAN_GROUP_ID_BY_CODE, ORGANIZATION_SECTOR_CHOICES, DONOR_SECTOR_CHOICES, APP_TYPE_CHOICES
from db.choices import SUBMISSION_SOURCE_CHOICES
from helpers.location import geos_location_from_coordinates
from helpers.diceware import diceware
from helpers.datetime import timediff
from jobs.messages import send_email, send_pretty_email


action_fields = [
    'locality', 'action_type', 'desc', 'target', 'unit_of_measurement',
    'progress', 'budget', 'start_date', 'end_date', 'published',
]

donation_fields = ['action', 'donor', 'amount', 'received_date', 'desc']


class EmailNotification(BaseModel):
    email_type = models.TextField()
    args = JSONField(help_text='Arguments for notification function')
    wait_hours = models.IntegerField(blank=True, default=0)
    period_hours = models.IntegerField()
    target = models.IntegerField(null=True, blank=True, db_index=True)
    sent = models.IntegerField(blank=True, default=0, db_index=True)
    last_sent = models.DateTimeField(blank=True, null=True, db_index=True)
    done = models.BooleanField(blank=True, default=False, db_index=True)
    pretty = models.BooleanField(blank=True, default=True)

    class Meta:
        unique_together = ('email_type', 'args')
        ordering = ('done', '-last_sent')

    def should_send(self):
        hours = timediff(timezone.now(), self.created, fmt='h')
        if hours < self.wait_hours:
            return False
        if self.done:
            return False
        if self.last_sent is None:
            return True
        return timediff(timezone.now(), self.last_sent, fmt='h') > self.period_hours

    def increment_sent(self):
        self.sent += 1
        if self.target is not None and self.sent >= self.target:
            self.done = True
        self.last_sent = timezone.now()
        self.save()


class AppVersion(BaseModel):
    app_type = models.TextField(choices=APP_TYPE_CHOICES, db_index=True)
    git_hash = models.TextField(db_index=True)

    @property
    def git_hash_short(self):
        return self.git_hash[:7]

    class Meta:
        ordering = ('-created',)


class Locality(BaseModel):
    """INEGI's "localidad". Loaded from external source.
    """
    cvegeo = models.TextField(unique=True)
    cvegeo_municipality = models.TextField(db_index=True)
    cvegeo_state = models.TextField(db_index=True)
    name = models.TextField()
    municipality_name = models.TextField()
    state_name = models.TextField()
    location = models.PointField()
    elevation = models.FloatField(null=True, blank=True)
    has_data = models.BooleanField(blank=True, default=False, db_index=True, help_text='Has additional data')
    meta = JSONField(default={}, blank=True, help_text='Metrics, file URLs, etc')

    REPR_FIELDS = ['cvegeo', 'name', 'municipality_name', 'state_name']
    STR_FIELDS = ['cvegeo', 'name', 'municipality_name', 'state_name']

    class Meta:
        indexes = [
            models.Index(fields=['location']),
        ]

    def save(self, *args, **kwargs):
        self.cvegeo_municipality = self.cvegeo[:5]
        self.cvegeo_state = self.cvegeo[:2]
        self.has_data = bool(self.meta.get('total'))
        return super().save(*args, **kwargs)


class ScianGroup(BaseModel):
    name = models.TextField()
    description = models.TextField(blank=True)


class Establishment(BaseModel):
    """Establishments loaded from DENUE.
    """
    cvegeo = models.TextField(blank=True)
    scian_group = models.ForeignKey('ScianGroup', default=1)
    locality = models.ForeignKey('Locality', null=True, blank=True)
    location = models.PointField(blank=True)

    # verbatim DENUE fields
    denue_id = models.TextField(unique=True)
    nom_estab = models.TextField(blank=True)
    raz_social = models.TextField(blank=True)

    codigo_act = models.TextField(blank=True, help_text='CVE_SCIAN')
    nombre_act = models.TextField(blank=True, help_text='DESC_SCIAN')

    per_ocu = models.TextField(blank=True)
    tipo_vial = models.TextField(blank=True)
    nom_vial = models.TextField(blank=True)
    tipo_v_e_1 = models.TextField(blank=True)
    nom_v_e_1 = models.TextField(blank=True)
    tipo_v_e_2 = models.TextField(blank=True)
    nom_v_e_2 = models.TextField(blank=True)
    tipo_v_e_3 = models.TextField(blank=True)
    nom_v_e_3 = models.TextField(blank=True)
    numero_ext = models.TextField(blank=True)
    letra_ext = models.TextField(blank=True)
    edificio = models.TextField(blank=True)
    edificio_e = models.TextField(blank=True)
    numero_int = models.TextField(blank=True)
    letra_int = models.TextField(blank=True)
    tipo_asent = models.TextField(blank=True)
    nomb_asent = models.TextField(blank=True)
    tipoCenCom = models.TextField(blank=True)
    nom_CenCom = models.TextField(blank=True)
    num_local = models.TextField(blank=True)
    cod_postal = models.TextField(blank=True)
    cve_ent = models.TextField(blank=True)
    entidad = models.TextField(blank=True)
    cve_mun = models.TextField(blank=True)
    municipio = models.TextField(blank=True)
    cve_loc = models.TextField(blank=True)
    localidad = models.TextField(blank=True)
    ageb = models.TextField(blank=True)
    manzana = models.TextField(blank=True)
    telefono = models.TextField(blank=True)
    correoelec = models.TextField(blank=True)
    www = models.TextField(blank=True)
    tipoUniEco = models.TextField(blank=True)
    latitud = models.TextField(blank=True)
    longitud = models.TextField(blank=True)
    fecha_alta = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['cvegeo']),
            models.Index(fields=['location']),
            models.Index(fields=['codigo_act']),
            models.Index(fields=['locality_id', 'scian_group_id']),
        ]

    def save(self, *args, **kwargs):
        self.cvegeo = ''.join(c.strip() for c in [self.cve_ent, self.cve_mun, self.cve_loc])
        self.locality = Locality.objects.filter(cvegeo=self.cvegeo).first()
        self.scian_group_id = SCIAN_GROUP_ID_BY_CODE.get(self.codigo_act, 1)
        try:
            self.location = geos_location_from_coordinates(float(self.latitud), float(self.longitud))
        except:  # don't save records without location
            return
        return super().save(*args, **kwargs)


class Municipality(BaseModel):
    """INEGI's "municipality". Loaded from external source.
    """
    cvegeo_municipality = models.TextField(unique=True)
    cvegeo_state = models.TextField(db_index=True)
    municipality_name = models.TextField()
    state_name = models.TextField()
    meta = JSONField(default={}, blank=True, help_text='Metrics, file URLs, etc')

    REPR_FIELDS = ['cvegeo_municipality', 'municipality_name', 'state_name']

    def save(self, *args, **kwargs):
        self.cvegeo_state = self.cvegeo_municipality[:2]
        return super().save(*args, **kwargs)


class State(BaseModel):
    """INEGI's "municipality". Loaded from external source.
    """
    cvegeo_state = models.TextField(unique=True)
    state_name = models.TextField()
    meta = JSONField(default={}, blank=True, help_text='Metrics, file URLs, etc')

    REPR_FIELDS = ['cvegeo_state', 'state_name']


def generate_secret_key():
    while True:
        secret_key = diceware(3, '.')
        if not Organization.objects.filter(secret_key=secret_key).exists():
            return secret_key


class Organization(BaseModel):
    """A reconstruction actor or data-gathering organization.
    """
    secret_key = models.TextField(unique=True, blank=True)
    sector = models.TextField(choices=ORGANIZATION_SECTOR_CHOICES, db_index=True)
    name = models.TextField(unique=True)
    desc = models.TextField(blank=True)
    year_established = models.IntegerField(null=True, blank=True)
    contact = JSONField(default={}, blank=True, help_text='Contact data')

    REPR_FIELDS = ['name', 'desc']
    STR_FIELDS = ['name', 'id', 'secret_key']

    class Meta:
        ordering = ('name',)

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.secret_key:
            self.secret_key = generate_secret_key()
        if not self.pk:
            super().save(*args, **kwargs)

            EmailNotification.objects.create(
                email_type='organization_no_projects',
                args={'organization_id': self.pk},
                wait_hours=24*3,
                period_hours=24*7,
                target=2,
            )
            EmailNotification.objects.create(
                email_type='organization_no_donations',
                args={'organization_id': self.pk},
                period_hours=24*6,
                target=2,
            )
            EmailNotification.objects.create(
                email_type='organization_no_photos',
                args={'organization_id': self.pk},
                period_hours=24*7,
                target=2,
            )

            return
        return super().save(*args, **kwargs)

    def clean(self):
        if not isinstance(self.contact, dict):
            raise ValidationError({'contact': 'must be instance of dict'})

    def reset_secret_key(self):
        self.secret_key = generate_secret_key()
        self.save()

    def score(self):
        base_score = 4
        return sum(pow(base_score + action.score, 0.75) for action in self.action_set.all())


class AbstractAction(models.Model):
    """For fields common to `Action` and `ActionLog` tables.
    """
    locality = models.ForeignKey('Locality')
    action_type = models.TextField()
    desc = models.TextField()
    target = models.FloatField(null=True, blank=True, help_text='How many units does action intend to deliver?')
    unit_of_measurement = models.TextField(blank=True)
    progress = models.FloatField(null=True, blank=True, help_text='How many units have been delivered?')
    budget = models.FloatField(null=True, blank=True, help_text='$MXN')
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    published = models.BooleanField(blank=True, default=True, db_index=True)
    archived = models.BooleanField(blank=True, default=False, db_index=True)

    class Meta:
        abstract = True


class Action(AbstractAction, BaseModel):
    """Action related to reconstruction.
    """
    key = models.IntegerField(blank=True, help_text="Auto-incremented number for actions in organization")
    organization = models.ForeignKey('Organization', help_text='Frozen after first read')
    image_count = models.IntegerField(default=0, blank=True)

    STR_FIELDS = ['locality_id', 'organization_id', 'action_type']

    class Meta:
        unique_together = ('key', 'organization')
        ordering = ('-end_date', '-start_date', '-modified')

    def save(self, *args, **kwargs):
        if self.pk is not None:
            return super().save(*args, **kwargs)
        max_key = Action.objects.filter(organization=self.organization).aggregate(Max('key'))
        self.key = (max_key.get('key__max') or 0) + 1
        while True:
            try:
                return super().save(*args, **kwargs)
            except IntegrityError as e:
                self.key += 1

    def calculate_image_count(self):
        return sum(len(s.synced_images(exclude_hidden=True)) for s in self.submission_set.filter(published=True))

    @property
    def score(self):
        if not self.published:
            return 0

        def budget_multiplier():
            if self.budget is None:
                return 0
            levels = [30000, 100000, 300000, 1000000, 3000000, 10000000, 30000000, 100000000]
            for i, l in enumerate(levels):
                if self.budget < l:
                    return i
            return len(levels)

        return pow(self.image_count, 0.6) * (
            1 +
            budget_multiplier() +
            1 if self.target is not None and self.progress is not None and self.unit_of_measurement else 0 +
            1 if self.start_date and self.end_date else 0
        )


class ActionLog(AbstractAction, BaseModel):
    """Log that tracks state of `Action`s. Each time we read a record from action
    source (e.g. spreadsheet), we add another record to this table.
    """
    action = models.ForeignKey('Action')


@receiver(models.signals.pre_save, sender=Action)
def create_action_log_record(sender, instance, **kwargs):
    if instance.pk is None:
        return
    old = Action.objects.get(pk=instance.pk)
    if any(getattr(old, f) != getattr(instance, f) for f in action_fields):
        ActionLog.objects.create(action=instance, **{f: getattr(instance, f) for f in action_fields})


@receiver(models.signals.post_save, sender=Action)
def create_first_action_log_record(sender, instance, created, **kwargs):
    if not created:
        return
    ActionLog.objects.create(action=instance, **{f: getattr(instance, f) for f in action_fields})


class Submission(BaseModel):
    """Submitted platform via mobile app.
    """
    location = models.PointField(null=True, blank=True)
    organization = models.ForeignKey('Organization', null=True, blank=True)
    action = models.ForeignKey('Action', null=True, blank=True)
    desc = models.TextField(blank=True, help_text='Can complement description inside of `data`')
    addr = models.TextField(blank=True, help_text='Can complement address inside of `data`')
    data = JSONField(default={}, blank=True, help_text='Submission data and metadata')
    source_id = models.IntegerField(blank=True, null=True)
    source = models.TextField(choices=SUBMISSION_SOURCE_CHOICES)
    submitted = models.DateTimeField(default=timezone.now, blank=True)
    images = JSONField(default=[], blank=True)
    published = models.BooleanField(blank=True, default=True, db_index=True)
    archived = models.BooleanField(blank=True, default=False, db_index=True)

    REPR_FIELDS = ['organization_id', 'action_id', 'submitted']

    class Meta:
        ordering = ('-submitted',)
        unique_together = ('source', 'source_id')
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['submitted']),
        ]

    @property
    def description(self):
        if self.desc:
            return self.desc
        try:
            return self.data['description']
        except:
            return ''

    @property
    def address(self):
        if self.desc:
            return self.addr
        try:
            return self.data['address']
        except:
            return ''

    @transaction.atomic
    def save(self, *args, **kwargs):
        from jobs.kobo import upload_submission_images
        from jobs.files import sync_submission_image_meta

        if self.action and self.action.organization != self.organization:
            self.action = None

        old_action = None
        created = self.pk is None
        if not created:
            old = Submission.objects.get(pk=self.pk)
            old_action = old.action
        new_action = self.action

        super().save(*args, **kwargs)
        if old_action:
            old_action.image_count = old_action.calculate_image_count()
            old_action.save()
        if new_action and new_action != old_action:
            new_action.image_count = new_action.calculate_image_count()
            new_action.save()

        if created:
            if self.source == 'kobo':
                upload_submission_images.delay(self.pk)
            else:
                sync_submission_image_meta.delay(self.pk)

    def synced_images(self, exclude_hidden=False):
        images = [i for i in self.images if i.get('hidden') is not True] if exclude_hidden else self.images

        # exclude certain fields, e.g. str representation of exif data
        def prepare_image(image):
            modified_image = {k: image[k] for k in image if k not in ['exif']}
            if image.get('height') and image.get('width') and image.get('rotate', 0) % 2 != 0:
                modified_image['width'] = image['height']
                modified_image['height'] = image['width']
            return modified_image

        bucket = os.getenv('CUSTOM_AWS_STORAGE_BUCKET_NAME')
        return [prepare_image(i) for i in images if i['url'].startswith(f'https://{bucket}.s3.amazonaws.com')]


class Donor(BaseModel):
    """A reconstruction donor.
    """
    sector = models.TextField(choices=DONOR_SECTOR_CHOICES, blank=True, db_index=True)
    name = models.TextField(unique=True)
    desc = models.TextField(blank=True)
    year_established = models.IntegerField(null=True, blank=True)
    contact = JSONField(default={}, blank=True, help_text='Contact data')
    donating = models.BooleanField(blank=True, default=False, db_index=True)
    donating_desc = models.TextField(blank=True)
    organization = models.OneToOneField('Organization', related_name='donor', blank=True, null=True,
                                        help_text='Is donor also an organization?')

    REPR_FIELDS = ['name', 'desc']
    STR_FIELDS = ['name', 'id']

    class Meta:
        ordering = ('name',)

    def clean(self):
        if not isinstance(self.contact, dict):
            raise ValidationError({'contact': 'must be instance of dict'})

    def add_contact_email(self, contact_email):
        contact_emails = self.contact.get('contact_emails', [])
        contact_emails.append(contact_email)
        self.contact['contact_emails'] = list(set(contact_emails))
        self.save()


class Donation(BaseModel):
    """A reconstruction donation.
    """
    action = models.ForeignKey('Action')
    donor = models.ForeignKey('Donor')
    amount = models.FloatField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True, db_index=True)
    desc = models.TextField(blank=True)
    approved_by_donor = models.BooleanField(blank=True, default=False, db_index=True)
    approved_by_org = models.BooleanField(blank=True, default=False, db_index=True)

    class Meta:
        ordering = ('-id',)

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Approves donations created by org user if no donor user exists yet.
        Unpublishes donations updated by either org or donor if there are any
        changes to donation.
        """
        from jobs.notifications import notification_function_by_email_type

        saved_by = kwargs.pop('saved_by', None)
        donor_has_users = len(self.donor.donoruser_set.all()) > 0
        email_type = None
        notification_args = None

        if self.pk is None:
            if saved_by == 'donor':
                self.approved_by_org = False
            if saved_by == 'org':
                self.approved_by_donor = not donor_has_users
            super().save(*args, **kwargs)  # save instance first so pk isn't `None`

            if saved_by == 'donor':
                email_type = 'donation_unapproved'
                notification_args = {'donation_id': self.pk, 'notify': 'org', 'created': True}
            if saved_by == 'org':
                if donor_has_users:
                    email_type = 'donation_unapproved'
                    notification_args = {'donation_id': self.pk, 'notify': 'donor', 'created': True}
                else:
                    email_type = 'donor_unclaimed'
                    notification_args = {'donation_id': self.pk}
        else:
            old = Donation.objects.get(pk=self.pk)
            if any(getattr(old, f) != getattr(self, f) for f in donation_fields):
                if saved_by == 'donor':
                    self.approved_by_org = False
                    email_type = 'donation_unapproved'
                    notification_args = {'donation_id': self.pk, 'notify': 'org', 'created': False}
                if saved_by == 'org':
                    self.approved_by_donor = not donor_has_users
                    if donor_has_users:
                        email_type = 'donation_unapproved'
                        notification_args = {'donation_id': self.pk, 'notify': 'donor', 'created': False}
                    else:
                        email_type = 'donor_unclaimed'
                        notification_args = {'donation_id': self.pk}
            super().save(*args, **kwargs)  # save instance before sending notifications so field values are updated

        if email_type and notification_args:
            pretty = email_type == 'donor_unclaimed'
            EmailNotification.objects.create(
                email_type=email_type,
                args=notification_args,
                wait_hours=24*3,
                period_hours=24*3,
                target=1,
                pretty=pretty,
            )
            for kwargs_set in notification_function_by_email_type[email_type](**notification_args):
                if pretty:
                    send_pretty_email.delay(**kwargs_set)
                else:
                    send_email.delay(**kwargs_set)


class VolunteerOpportunity(BaseModel):
    action = models.ForeignKey('Action')
    name_of_position = models.TextField()
    required_skills = ArrayField(models.TextField())
    desc = models.TextField()
    from_anywhere = models.BooleanField()
    location_desc = models.TextField(blank=True)
    transport_included = models.BooleanField(blank=True, default=False)
    food_included = models.BooleanField(blank=True, default=False)
    target = models.FloatField(help_text='How many volunteers does this project need?')
    progress = models.FloatField(blank=True, default=0, help_text='How many volunteers have signed up?')
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    published = models.BooleanField(blank=True, default=True, db_index=True)

    class Meta:
        ordering = ('-created',)


class VolunteerApplication(BaseModel):
    opportunity = models.ForeignKey('VolunteerOpportunity')
    user = models.ForeignKey('users.VolunteerUser')
    reason_why = models.TextField()
    days_volunteered = models.IntegerField(blank=True, default=0)
