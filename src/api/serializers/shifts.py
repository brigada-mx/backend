from django.core.urlresolvers import reverse
from django.conf import settings

from rest_framework import serializers

from database.reservations.models import Shift, ShiftIncident, ShiftSignature
from api.mixins import EagerLoadingMixin, DynamicFieldsMixin
from api.fields import LatLngField
from api.serializers import ReservationSerializer
from .care import CareLogEntrySerializer
from .nurses import NurseUserSerializer
from .clients import ClientUserSerializer


class ShiftIncidentSerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    """For reading and updating `ShiftIncident` instances. `nurse` and `shift`
    are read only.
    """
    _SELECT_RELATED_FIELDS = ['shift', 'nurse',]

    url = serializers.HyperlinkedIdentityField(view_name='api:shiftincident-detail')
    shift = serializers.HyperlinkedRelatedField(view_name='api:shift-detail', read_only=True)
    nurse = serializers.HyperlinkedRelatedField(view_name='api:nurse-detail', read_only=True)
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = ShiftIncident
        fields = '__all__'

    def get_category_name(self, obj):
        return obj.get_category_display()


class ShiftSignatureSerializer(serializers.ModelSerializer):
    signature = serializers.CharField(max_length=1000000)

    class Meta:
        model = ShiftSignature
        exclude = ('created', 'modified', 'shift', 'signature')


class ShiftSerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    """Inheriting from HyperlinkedModelSerializer requires that appropriate
    detail views exist for all foreign key fields.

    Explicitly uses NurseUserSerializer for nested NurseUser representation,
    because default nurse serializer results in N+1 query behavior, even with
    depth=1. This will happen with any model that has a many-many relationship
    or reverse FK relationship.
    """
    _SELECT_RELATED_FIELDS = ['reservation', 'nurse', 'address', 'shiftsignature']
    _PREFETCH_RELATED_FIELDS = ['patients', 'reservation__clientuser_set',]

    url = serializers.HyperlinkedIdentityField(view_name='api:shift-detail')
    care_log_entries_url = serializers.HyperlinkedIdentityField(view_name='api:carelogentry-list-shift')
    url_admin = serializers.SerializerMethodField()
    nurse = NurseUserSerializer(read_only=True)
    reservation = ReservationSerializer(read_only=True)
    reservation_url_admin = serializers.SerializerMethodField()
    care_log_entries = serializers.CharField(read_only=True)
    duration = serializers.SerializerMethodField()
    location = LatLngField()

    patients = serializers.HyperlinkedRelatedField(many=True, view_name='api:patient-detail', read_only=True)
    patient_names = serializers.SerializerMethodField()
    patient_phones = serializers.SerializerMethodField()
    clients = ClientUserSerializer(source='clientuser_set', many=True, read_only=True)
    client_names = serializers.SerializerMethodField()
    client_phones = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()
    shiftsignature = ShiftSignatureSerializer(read_only=True)

    class Meta:
        model = Shift
        fields = '__all__'
        depth = 1

    def __init__(self, *args, **kwargs):
        if 'context' in kwargs:
            request = kwargs['context']['request']
            if request.auth is 'NurseUser':
                self.fields.pop('incidents', None)
            else:
                self.fields.pop('nurse_incidents', None)
        super(ShiftSerializer, self).__init__(*args, **kwargs)

    def get_duration(self, obj):
        return obj.total_hours

    def get_patient_names(self, obj):
        return [patient.full_name for patient in obj.patients.all()]

    def get_patient_phones(self, obj):
        return [patient.phone for patient in obj.patients.all() if patient.phone]

    def get_client_names(self, obj):
        return [client.full_name for client in obj.clientuser_set.all()]

    def get_client_phones(self, obj):
        return [client.phone for client in obj.clientuser_set.all() if client.phone]

    def get_full_address(self, obj):
        return obj.address.full_address

    def get_url_admin(self, obj):
        return "{}{}".format(settings.SITE_URL,
                             reverse('staff:accounts:shifts:update', args=[obj.reservation_id, obj.pk]))

    def get_reservation_url_admin(self, obj):
        return "{}{}".format(settings.SITE_URL, reverse('staff:accounts:detail', args=[obj.reservation_id]))


class ShiftDetailSerializer(ShiftSerializer):
    """Like `ShiftSerializer`, with additional URLs pointing to various
    "shift_actions", and additional nested resources related to the shift.
    """
    _PREFETCH_RELATED_FIELDS = ['carelogentry_set__task', 'patients', 'reservation__clientuser_set',]

    care_log_entries = CareLogEntrySerializer(source='carelogentry_set', many=True, read_only=True) # reverse FK relationship
    incidents = ShiftIncidentSerializer(source='shiftincident_set', many=True, read_only=True) # reverse FK relationship
    incidents_url = serializers.HyperlinkedIdentityField(view_name='api:shiftincident-list-shift')
    nurse_incidents = ShiftIncidentSerializer(source='shiftincident_set.for_nurse_user', many=True, read_only=True) # uses custom manager

    action_cancel = serializers.HyperlinkedIdentityField(view_name='api:shift-cancel')
    action_checkin = serializers.HyperlinkedIdentityField(view_name='api:shift-checkin')
    action_checkout = serializers.HyperlinkedIdentityField(view_name='api:shift-checkout')
    action_incident = serializers.HyperlinkedIdentityField(view_name='api:shiftincident')

    care_log_completion = serializers.SerializerMethodField()

    def get_care_log_completion(self, obj):
        return obj.care_log_completion


class ShiftNurseSubsetSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    """Serializes a subset of `Shift` fields without revealing sensitive
    information to nurses, e.g. for serializing past shifts.
    """
    _PREFETCH_RELATED_FIELDS = ['carelogentry_set__task',]

    duration = serializers.SerializerMethodField()
    care_log_completion = serializers.SerializerMethodField()

    class Meta:
        model = Shift
        fields = ('id', 'start', 'end', 'checkin', 'checkout', 'duration', 'care_log_completion',)

    def get_duration(self, obj):
        return obj.total_hours

    def get_care_log_completion(self, obj):
        return obj.care_log_completion
