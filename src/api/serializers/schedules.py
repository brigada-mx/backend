from django.db import transaction

from rest_framework.reverse import reverse
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from database.reservations.models import ShiftSchedule, ShiftScheduleDay, ShiftSchedulePostingResponse
from database.nurses.models import NurseReservationConnection
from api.mixins import EagerLoadingMixin, DynamicFieldsMixin


class ShiftScheduleDaySerializerMixin:
    _SELECT_RELATED_FIELDS = ['shift_schedule__address', 'nurse',]
    _PREFETCH_RELATED_FIELDS = ['shift_schedule__shiftscheduleday_set',]

    nurse = serializers.HyperlinkedRelatedField(view_name='api:nurse-detail', read_only=True)
    rates = serializers.SerializerMethodField()
    day_name = serializers.SerializerMethodField()
    nurse_name = serializers.SerializerMethodField()
    zone = serializers.SerializerMethodField()
    required_nurse_type_name = serializers.SerializerMethodField()
    reservation_id = serializers.SerializerMethodField()

    def get_day_name(self, obj):
        return obj.get_day_display()

    def get_nurse_name(self, obj):
        return obj.nurse.full_name if obj.nurse else ''

    def get_zone(self, obj):
        return obj.shift_schedule.address.zone

    def get_required_nurse_type_name(self, obj):
        return obj.shift_schedule.get_required_nurse_type_display()

    def get_reservation_id(self, obj):
        return obj.shift_schedule.reservation_id


class ShiftScheduleDaySerializer(serializers.ModelSerializer, ShiftScheduleDaySerializerMixin, EagerLoadingMixin):
    class Meta:
        model = ShiftScheduleDay
        exclude = ('created', 'modified',)


class ShiftScheduleDayWithoutShiftScheduleSerializer(serializers.ModelSerializer,
                                                    ShiftScheduleDaySerializerMixin, EagerLoadingMixin):
    class Meta:
        model = ShiftScheduleDay
        exclude = ('created', 'modified', 'shift_schedule')


class ShiftScheduleSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['address',]
    _PREFETCH_RELATED_FIELDS = ['patients', 'shiftscheduleday_set__nurse']

    url = serializers.HyperlinkedIdentityField(view_name='api:shiftschedule-detail')
    shift_schedule_days = ShiftScheduleDayWithoutShiftScheduleSerializer(many=True, source='shiftscheduleday_set')
    url_admin = serializers.SerializerMethodField()
    url_client = serializers.SerializerMethodField()

    class Meta:
        model = ShiftSchedule
        exclude = ('created', 'modified',)
        read_only_fields = ('reservation',)

    zone = serializers.SerializerMethodField()
    required_nurse_type_name = serializers.SerializerMethodField()
    patients = serializers.SerializerMethodField()
    reservation_status_name = serializers.SerializerMethodField()

    def get_zone(self, obj):
        """Give nurse an idea of where service is, but nothing more.
        """
        return obj.address.zone

    def get_required_nurse_type_name(self, obj):
        return obj.get_required_nurse_type_display()

    def get_patients(self, obj):
        """Limited information about patients: `gender` and `birth` (age).
        """
        return [{'age': patient.age, 'gender': patient.gender} for patient in obj.patients.all()]

    def get_url_admin(self, obj):
        return reverse('staff:accounts:schedules:update',
                       args=[obj.reservation_id, obj.pk], request=self.context.get('request'))

    def get_url_client(self, obj):
        return reverse('clients:shift-schedule-update', args=[obj.pk], request=self.context.get('request'))

    def get_reservation_status_name(self, obj):
        return obj.reservation.get_status_display()

    def validate(self, validated_data):
        """If client user is making request, make sure the address and nurses they
        are setting belong to or are connected to their account.
        """
        request = self.context.get('request')
        if not request or not request.user.is_client:
            return validated_data

        reservation = request.user.reservation
        address, days = validated_data.get('address'), validated_data.get('shiftscheduleday_set')
        if address and not address.reservation == reservation:
            raise ValidationError('Error: this address does not belong to this account: {}'.format(address))
        for day in days:
            nurse = day.get('nurse')
            if nurse and not nurse in NurseReservationConnection.get_nurses(reservation):
                raise ValidationError('Error: this nurse does not belong to this account: {}'.format(nurse))
        return validated_data

    def create(self, validated_data):
        """Create the `ShiftSchedule` and its corresponding `ShiftScheduleDay`s
        after data is validated."""
        days_data = validated_data.pop('shiftscheduleday_set')
        shift_schedule = ShiftSchedule.objects.create(**validated_data)

        for day_data in days_data:
            try:
                ShiftScheduleDay.objects.create(shift_schedule=shift_schedule, **day_data)
            except:
                shift_schedule.delete()
                raise

        return shift_schedule

    def update(self, instance, validated_data):
        with transaction.atomic(): # ensures delete isn't committed if creation fails after
            instance.shiftscheduleday_set.all().delete() # hacky but correct, and much easier to implement
            days_data = validated_data.pop('shiftscheduleday_set')

            for key in validated_data:
                setattr(instance, key, validated_data[key])

            for day_data in days_data:
                ShiftScheduleDay.objects.create(shift_schedule=instance, **day_data)

            instance.save()
        return instance


class ShiftSchedulePostingResponseSerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['shift_schedule_posting__shift_schedule__address', 'nurse',]
    _PREFETCH_RELATED_FIELDS = ['shift_schedule_posting__shift_schedule__shiftscheduleday_set__nurse',
                                'shift_schedule_posting__shift_schedule__patients',]

    nurse = serializers.HyperlinkedRelatedField(view_name='api:nurse-detail', read_only=True)
    shift_schedule_posting_respond = serializers.HyperlinkedIdentityField(view_name='api:shiftscheduleposting-respond')
    shift_schedule = serializers.SerializerMethodField()
    days = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = ShiftSchedulePostingResponse
        fields = '__all__'

    def get_shift_schedule(self, obj):
        return ShiftScheduleSerializer(
            obj.shift_schedule_posting.shift_schedule, many=False, read_only=True, context=self.context,
        ).data

    def get_days(self, obj):
        return obj.shift_schedule_posting.days

    def get_start_date(self, obj):
        return obj.shift_schedule_posting.start_date

    def get_end_date(self, obj):
        return obj.shift_schedule_posting.end_date

    def get_description(self, obj):
        return obj.shift_schedule_posting.description
