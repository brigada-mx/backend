from django.contrib.gis.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField

from db.config import BaseModel
from db.choices import ACTION_SOURCE_CHOICES, CODE_SCIAN_GROUP_ID, ORGANIZATION_SECTOR_CHOICES
from helpers.location import geos_location_from_coordinates


class Locality(BaseModel):
    """INEGI's "localidad". Loaded from external source.
    """
    cvegeo = models.TextField(unique=True)
    cvegeo_municipality = models.TextField(db_index=True)
    cvegeo_state = models.TextField(db_index=True)
    name = models.TextField()
    municipality_name = models.TextField()
    state_name = models.TextField()
    location = models.PointField(null=False)
    elevation = models.FloatField(null=True)
    has_data = models.BooleanField(default=False, db_index=True, help_text='Has additional data')
    meta = JSONField(default={}, help_text='Metrics, file URLs, etc')

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
    locality = models.ForeignKey('Locality', null=True)
    location = models.PointField(blank=True, null=True)

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
        except:
            self.location = None
        return super().save(*args, **kwargs)


class Municipality(BaseModel):
    """INEGI's "municipality". Loaded from external source.
    """
    cvegeo_municipality = models.TextField(unique=True)
    cvegeo_state = models.TextField(db_index=True)
    municipality_name = models.TextField()
    state_name = models.TextField()
    meta = JSONField(default={}, help_text='Metrics, file URLs, etc')

    REPR_FIELDS = ['cvegeo_municipality', 'municipality_name', 'state_name']

    def save(self, *args, **kwargs):
        self.cvegeo_state = self.cvegeo_municipality[:2]
        return super().save(*args, **kwargs)


class State(BaseModel):
    """INEGI's "municipality". Loaded from external source.
    """
    cvegeo_state = models.TextField(unique=True)
    state_name = models.TextField()
    meta = JSONField(default={}, help_text='Metrics, file URLs, etc')

    REPR_FIELDS = ['cvegeo_state', 'state_name']


class Organization(BaseModel):
    """A reconstruction actor or data-gathering organization.
    """
    key = models.TextField(unique=True, help_text='Essentially google sheet tab name')
    sector = models.TextField(choices=ORGANIZATION_SECTOR_CHOICES, db_index=True)
    name = models.TextField(blank=True)
    desc = models.TextField(blank=True)
    contact = JSONField(default={}, help_text='Contact data')

    REPR_FIELDS = ['key', 'name', 'desc']


class AbstractAction(models.Model):
    """For fields common to `Action` and `ActionLog` tables.
    """
    locality = models.ForeignKey('Locality')
    action_type = models.TextField(blank=True)
    desc = models.TextField(blank=True)
    target = models.FloatField(null=True, help_text='How many units does action intend to deliver')
    unit_of_measurement = models.TextField(blank=True)
    progress = models.FloatField(null=True, help_text='How many units have been delivered?')
    budget = models.FloatField(null=True, help_text='$MXN')
    start_date = models.DateField(null=True, db_index=True)
    end_date = models.DateField(null=True, db_index=True)

    class Meta:
        abstract = True


class Action(AbstractAction, BaseModel):
    """Action related to reconstruction. A new record in this table is generated
    for each new `key`.
    """
    key = models.TextField(help_text='Essentially google sheet row number')
    organization = models.ForeignKey('Organization', help_text='Frozen after first read')
    source = models.TextField(choices=ACTION_SOURCE_CHOICES)

    class Meta:
        unique_together = ('key', 'organization')


class ActionLog(AbstractAction, BaseModel):
    """Log that tracks state of `Action`s. Each time we read a record from action
    source (e.g. spreadsheet), we add another record to this table.
    """
    action = models.ForeignKey('Action')


class Observer(BaseModel):
    """User of the observation mobile app, NOT a user of this application.
    """
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)


class Observation(BaseModel):
    """Observation uploaded to platform via mobile app.
    """
    locality = models.ForeignKey('Locality')
    observer = models.ForeignKey('Observer', blank=True)
    location = models.PointField(null=False)
    data = JSONField(help_text='Observation form data, such as description, type, file URLs')
    source_id = models.TextField(help_text="Identifier for observation's source")
    schema_id = models.TextField(help_text="Identifier for observation's schema")
    recorded = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['recorded']),
        ]


class OrganizationObservation(BaseModel):
    """Observation from data-gathering organization, defined for a certain point
    or for a locality.
    """
    locality = models.ForeignKey('Locality')
    generator = models.ForeignKey('Organization', help_text='Organization that generated this observation')
    location = models.PointField(null=True)
    data = JSONField(help_text='Data for this observation, generated by DS')
    version = models.TextField(help_text='Lets DS change structure without breaking clients')
    data_set = models.TextField(help_text='Data set/source of this observation')
    recorded = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['recorded']),
        ]
