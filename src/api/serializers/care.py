from django.db import transaction

from rest_framework import serializers
from rest_framework.reverse import reverse

from database.patients.models import CareTask, CareLogEntry, CareSchedule, CareScheduleTask, NurseCareScheduleTask, CareCircleMember
from api.mixins import EagerLoadingMixin, DynamicFieldsMixin


class CareTaskSerializer(serializers.ModelSerializer):
    observations_schema = serializers.JSONField()
    observations_options = serializers.JSONField()

    task_name = serializers.SerializerMethodField()

    class Meta:
        model = CareTask
        fields = '__all__'

    def get_task_name(self, obj):
        return obj.get_task_display()


class CareLogEntrySerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['task', 'shift', 'patient',]

    url = serializers.HyperlinkedIdentityField(view_name='api:carelogentry-detail')
    shift = serializers.HyperlinkedRelatedField(view_name='api:shift-detail', read_only=True)
    patient = serializers.HyperlinkedRelatedField(view_name='api:patient-detail', read_only=True)
    task = CareTaskSerializer(read_only=True)
    time_order = serializers.IntegerField(required=False)

    observations = serializers.JSONField()
    instructions = serializers.JSONField()

    observations_completed = serializers.SerializerMethodField()
    status_name = serializers.SerializerMethodField()
    patient_id = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = CareLogEntry
        read_only_fields = ('task', 'time_order', 'shift_day', 'created_by_nurse', 'schedule', 'patient_name',
                            'instructions', 'additional_instructions', 'observations_completed', 'start',)
        exclude = ('patient',)

    def get_status_name(self, obj):
        return obj.get_status_display()

    def get_observations_completed(self, obj):
        """Returns `None`, `True` or `False`.
        """
        return bool(obj.observations)

    def get_patient_id(self, obj):
        """For reasons unknown to me, including `patient` causes the DRF
        validator to raise an integrity error -- it tries to create a new object
        with the same natural key instead of updating the instance. This method
        is a substitute.

        Related to this issue:
        https://github.com/tomchristie/django-rest-framework/issues/2380
        """
        return obj.patient_id

    def get_patient_name(self, obj):
        return obj.patient.full_name


class CareScheduleTaskSerializer(serializers.ModelSerializer,):
    task = CareTaskSerializer(read_only=True)
    schedule = serializers.JSONField()

    class Meta:
        model = CareScheduleTask
        exclude = ('care_schedule',)


class CareScheduleSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_RELATED_FIELDS = ['carescheduletask_set__task',]
    care_schedule_tasks = CareScheduleTaskSerializer(source='carescheduletask_set',
                                                     many=True, read_only=True) # reverse FK relationship

    class Meta:
        model = CareSchedule
        fields = '__all__'


class CareScheduleTaskWriteSerializer(serializers.ModelSerializer):
    schedule = serializers.JSONField()

    class Meta:
        model = CareScheduleTask
        exclude = ('modified', 'care_schedule')


class CareScheduleCreateUpdateSerializer(serializers.ModelSerializer):
    care_schedule_tasks = CareScheduleTaskWriteSerializer(many=True, source='carescheduletask_set')
    url_client = serializers.SerializerMethodField()

    def get_url_client(self, obj):
        return reverse('clients:care-schedule-update', args=[obj.pk], request=self.context.get('request'))

    class Meta:
        model = CareSchedule
        exclude = ('modified',)
        read_only_fields = ('reservation',)

    def create(self, validated_data):
        tasks_data = validated_data.pop('carescheduletask_set')
        care_schedule = CareSchedule.objects.create(**validated_data)

        for task_data in tasks_data:
            try:
                CareScheduleTask.objects.create(care_schedule=care_schedule, **task_data)
            except:
                care_schedule.delete()
                raise

        return care_schedule

    def update(self, instance, validated_data):
        with transaction.atomic(): # ensures delete isn't committed if creation fails after
            instance.carescheduletask_set.all().delete() # hacky but correct
            tasks_data = validated_data.pop('carescheduletask_set')

            for key in validated_data:
                setattr(instance, key, validated_data[key])

            for task_data in tasks_data:
                CareScheduleTask.objects.create(care_schedule=instance, **task_data)

            instance.save()
        return instance


class CareSendReportSerializer(serializers.Serializer):
    min_date = serializers.DateField()
    max_date = serializers.DateField()


class CareSendReportCareCircleSerializer(CareSendReportSerializer):
    contact_types = serializers.MultipleChoiceField(choices=CareCircleMember.CONTACT_TYPE_CHOICES)


class NurseCareScheduleTaskSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['patient__reservation', 'nurse', 'task',]
    _PREFETCH_RELATED_FIELDS = ['patient__shift_set__nurse', 'patient__shift_schedules__shiftscheduleday_set__nurse']

    url = serializers.HyperlinkedIdentityField(view_name='api:nursecarescheduletask-detail')
    nurse = serializers.HyperlinkedRelatedField(view_name='api:nurse-detail', read_only=True)
    patient = serializers.HyperlinkedRelatedField(view_name='api:patient-detail', read_only=True)
    patient_id = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    task_id = serializers.SerializerMethodField()
    task_name = serializers.SerializerMethodField()
    instructions = serializers.JSONField()

    class Meta:
        model = NurseCareScheduleTask
        fields = '__all__'
        read_only_fields = ('task', 'patient_id', 'task_id',)

    def get_patient_name(self, obj):
        return obj.patient.full_name

    def get_patient_id(self, obj):
        return obj.patient.pk

    def get_task_id(self, obj):
        return obj.task.pk

    def get_task_name(self, obj):
        return obj.task.get_task_display()
