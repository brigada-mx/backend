from django.core.urlresolvers import reverse
from django.conf import settings

from rest_framework import serializers

from database.patients.models import Patient, Address, CareCircleMember
from api.mixins import EagerLoadingMixin, DynamicFieldsMixin
from api.serializers import CareScheduleSerializer, ShiftScheduleSerializer
from api.fields import LatLngField


class PatientFlatSerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['care_schedule', 'reservation']

    url = serializers.HyperlinkedIdentityField(view_name='api:patient-detail')
    url_admin = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ('id', 'url', 'url_admin', 'reservation', 'first_name', 'surname', 'gender', 'phone',
                  'care_schedule', 'created', 'modified', 'full_name', 'birth',)

    def get_url_admin(self, obj):
        return "{}{}".format(settings.SITE_URL,
                             reverse('staff:accounts:patients:update', args=[obj.reservation_id, obj.pk]))

    def get_full_name(self, obj):
        return obj.full_name


class PatientSerializer(PatientFlatSerializer):
    _PREFETCH_RELATED_FIELDS = ['shift_schedules',]

    class Meta(PatientFlatSerializer.Meta):
        """Including `depth = 1` in the parent class prevents it from being used
        to create a patient, because it prevents the `reservation` field from
        being writeable.
        """
        fields = PatientFlatSerializer.Meta.fields + ('shift_schedules',)
        depth = 1


class PatientDetailSerializer(PatientSerializer):
    _SELECT_RELATED_FIELDS = ['care_schedule',] # reduce number of prefetch queries by 1
    _PREFETCH_RELATED_FIELDS = ['care_schedule__carescheduletask_set__task', 'shift_schedules__shiftscheduleday_set']

    care_schedule = CareScheduleSerializer(read_only=True)
    shift_schedules = ShiftScheduleSerializer(read_only=True, many=True)
    # FIX: nesting `shift_schedule` as part of the serialized patient leads to N + 1 query behavior, create a `ShiftScheduleDaySubsetSerializer`, due to serializing `rates`

    class Meta(PatientSerializer.Meta):
        read_only_fields = ('reservation', 'created', 'modified',)


class AddressFlatSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['reservation',]

    url = serializers.HyperlinkedIdentityField(view_name='api:address-detail')
    location = LatLngField(required=False)

    class Meta:
        model = Address
        fields = ('id', 'url', 'reservation', 'address', 'indoor_number', 'zip_code', 'city', 'zone', 'location',)


class AddressSerializer(AddressFlatSerializer):
    class Meta(AddressFlatSerializer.Meta):
        depth = 1


class CareCircleMemberSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:care-circle-member-detail')

    full_name = serializers.SerializerMethodField()
    contact_type_name = serializers.SerializerMethodField()

    class Meta:
        model = CareCircleMember
        fields = '__all__'
        read_only_fields = ('reservation',)

    def get_contact_type_name(self, obj):
        return obj.get_contact_type_display()

    def get_full_name(self, obj):
        return obj.full_name


class CareCircleNotifySerializer(serializers.Serializer):
    body = serializers.CharField(required=True, allow_blank=False)
    contact_types = serializers.ListField(child=serializers.IntegerField(), required=False)
