from django.contrib.gis.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField

from db.config import BaseModel
from db.choices import ACTION_SOURCE_CHOICES


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
    meta = JSONField(default={}, help_text='Metrics, file URLs, etc')

    REPR_FIELDS = ['cvegeo', 'name', 'municipality_name', 'state_name']

    class Meta:
        indexes = [
            models.Index(fields=['location']),
        ]

    def save(self, *args, **kwargs):
        self.cvegeo_municipality = self.cvegeo[:5]
        self.cvegeo_state = self.cvegeo[:2]
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
