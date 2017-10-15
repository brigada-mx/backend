from django.utils import timezone

from rest_framework import serializers
from rest_framework.reverse import reverse

from database.reservations.models import Reservation

from api.mixins import EagerLoadingMixin


class ReservationSerializer(serializers.ModelSerializer):
    notify_care_circle_url = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = '__all__'

    def get_notify_care_circle_url(self, obj):
        return reverse('api:care-circle-notify', request=self.context.get('request'))


class ReservationDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_RELATED_FIELDS = ['shift_set',]

    previous_shift_date = serializers.SerializerMethodField()
    next_shift_date = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = '__all__'

    def get_previous_shift_date(self, obj):
        shift = obj.shift_set.filter(start__lt=timezone.now()).order_by('-start').first()
        return shift.start if shift else None

    def get_next_shift_date(self, obj):
        shift = obj.shift_set.filter(start__gt=timezone.now()).order_by('start').first()
        return shift.start if shift else None
