import os

from django.contrib.gis.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from django.dispatch import receiver

from db.config import BaseModel
from db.choices import ACTION_SOURCE_CHOICES, CODE_SCIAN_GROUP_ID, ORGANIZATION_SECTOR_CHOICES
from db.choices import SUBMISSION_SOURCE_CHOICES
from helpers.location import geos_location_from_coordinates
from helpers.diceware import diceware
from helpers.http import s3_thumbnail_url


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
    has_data = models.BooleanField(default=False, db_index=True, help_text='Has additional data')
    meta = JSONField(default={}, blank=True, help_text='Metrics, file URLs, etc')

    REPR_FIELDS = ['cvegeo', 'name', 'municipality_name', 'state_name']

    class Meta:
        indexes = [
            models.Index(fields=['location']),
        ]

    def save(self, *args, **kwargs):
        self.cvegeo_municipality = self.cvegeo[:5]
        self.cvegeo_state = self.cvegeo[:2]
        self.has_data = bool(self.meta)
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
        ]

    def save(self, *args, **kwargs):
        self.cvegeo = ''.join(c.strip() for c in [self.cve_ent, self.cve_mun, self.cve_loc])
        self.locality = Locality.objects.filter(cvegeo=self.cvegeo).first()
        self.scian_group_id = CODE_SCIAN_GROUP_ID.get(self.codigo_act, 1)
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
    key = models.TextField(unique=True, help_text='Essentially google sheet tab name')
    secret_key = models.TextField(unique=True, blank=True)
    sector = models.TextField(choices=ORGANIZATION_SECTOR_CHOICES, db_index=True)
    name = models.TextField()
    desc = models.TextField()
    year_established = models.IntegerField()
    contact = JSONField(default={}, blank=True, help_text='Contact data')

    REPR_FIELDS = ['key', 'name', 'desc']

    def save(self, *args, **kwargs):
        if not self.secret_key:
            self.secret_key = generate_secret_key()
        return super().save(*args, **kwargs)

    def reset_secret_key(self):
        self.secret_key = generate_secret_key()
        self.save()


class AbstractAction(models.Model):
    """For fields common to `Action` and `ActionLog` tables.
    """
    locality = models.ForeignKey('Locality')
    action_type = models.TextField()
    desc = models.TextField(blank=True)
    target = models.FloatField(null=True, blank=True, help_text='How many units does action intend to deliver')
    unit_of_measurement = models.TextField(blank=True)
    progress = models.FloatField(null=True, blank=True, help_text='How many units have been delivered?')
    budget = models.FloatField(null=True, blank=True, help_text='$MXN')
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    published = models.BooleanField(blank=True, default=True, db_index=True)

    class Meta:
        abstract = True


class PublicActionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(published=True)


class Action(AbstractAction, BaseModel):
    """Action related to reconstruction. A new record in this table is generated
    for each new `key`.
    """
    key = models.IntegerField(help_text='Essentially google sheet row number')
    organization = models.ForeignKey('Organization', help_text='Frozen after first read')
    source = models.TextField(choices=ACTION_SOURCE_CHOICES)
    objects = models.Manager()
    public_objects = PublicActionManager()

    class Meta:
        unique_together = ('key', 'organization')
        ordering = ('-end_date', '-start_date', '-modified')


class ActionLog(AbstractAction, BaseModel):
    """Log that tracks state of `Action`s. Each time we read a record from action
    source (e.g. spreadsheet), we add another record to this table.
    """
    action = models.ForeignKey('Action')


class Submission(BaseModel):
    """Submitted platform via mobile app.
    """
    location = models.PointField(null=True, blank=True)
    organization = models.ForeignKey('Organization')
    action = models.ForeignKey('Action', null=True, blank=True)
    data = JSONField(help_text='Submission data and metadata, such as description, type, file URLs')
    source_id = models.IntegerField()
    source = models.TextField(choices=SUBMISSION_SOURCE_CHOICES)
    submitted = models.DateTimeField(default=timezone.now, blank=True)
    image_urls = JSONField(default=[], blank=True)

    REPR_FIELDS = ['organization_id', 'action_id', 'submitted']

    class Meta:
        ordering = ('-submitted',)
        unique_together = ('source', 'source_id')
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['submitted']),
        ]

    def save(self, *args, **kwargs):
        if self.action and self.action.organization != self.organization:
            self.action = None
        return super().save(*args, **kwargs)

    def synced_image_urls(self):
        bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
        return [url for url in self.image_urls if url.startswith('https://{}.s3.amazonaws.com'.format(bucket))]

    def thumbnails(self, *args, **kwargs):
        return [s3_thumbnail_url(url, *args, **kwargs) for url in self.synced_image_urls()]


@receiver(models.signals.post_save, sender=Submission)
def auto_assign_care_shift_schedule(sender, instance, created, **kwargs):
    """Assign first care schedule and shift schedule are to patient on object
    creation.
    """
    from jobs.kobo import upload_submission_images
    if not created:
        return
    upload_submission_images.delay(instance.pk)
