from rest_framework import generics
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication

from database.patients.models import CareLogEntry
from database.nurses.models import NurseUser, Review
from database.clients.models import ClientUser
from database.reservations.models import Shift, ShiftSchedulePostingResponse
from api import backends
from api.filters import CareLogEntryFilter, ShiftFilter, PostingResponseFilter, NurseFilter, NurseReviewFilter, ClientFilter
from api.serializers import NurseReviewSerializer
from api.mixins import MetricsMixin


class CareLogEntryMetrics(generics.GenericAPIView, MetricsMixin):
    """Metrics related to completion of care log entries.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication, backends.ClientTokenAuthentication, backends.InternalAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    filter_class = CareLogEntryFilter # inheriting from `GenericAPIView` gives us filtering via `filter_class`

    FILTER_PARAMS = ('status', 'has_observations', 'created_by_nurse')
    GROUP_BY_PARAMS = (('group_by_month', 'shift__month'), ('group_by_nurse', 'shift__nurse'),
                       ('group_by_status', 'status'), ('group_by_task', 'task__task'), ('group_by_shift', 'shift'),
                       ('group_by_reservation', 'shift__reservation'),)
    ordering_fields = tuple(param[1] for param in GROUP_BY_PARAMS)

    def get_queryset(self):
        queryset = CareLogEntry.objects.all().select_related('task', 'shift',)
        if self.request.auth == "ClientUser":
            return queryset.filter(shift__reservation__clientuser=self.request.user).distinct()
        if self.request.auth == "NurseUser":
            return queryset.filter(shift__nurse=self.request.user).distinct()
        return queryset


class ShiftMetrics(generics.GenericAPIView, MetricsMixin):
    """Metrics related to checkins/checkouts.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication, backends.ClientTokenAuthentication, backends.InternalAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    filter_class = ShiftFilter

    FILTER_PARAMS = ('has_checkin', 'has_checkout', 'has_checkin_delay', 'max_checkin_delay')
    GROUP_BY_PARAMS = (('group_by_month', 'month'), ('group_by_nurse', 'nurse'))
    ordering_fields = tuple(param[1] for param in GROUP_BY_PARAMS)

    def get_queryset(self):
        queryset = Shift.objects.all().select_related('nurse', 'reservation')
        if self.request.auth == "ClientUser":
            return queryset.filter(reservation__clientuser=self.request.user).distinct()
        if self.request.auth == "NurseUser":
            return queryset.filter(nurse=self.request.user).distinct()
        return queryset


class PostingResponseMetrics(generics.GenericAPIView, MetricsMixin):
    """Metrics related to shift schedule posting responses.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    filter_class = PostingResponseFilter

    FILTER_PARAMS = ('can_cover', 'max_response_delay', 'has_responded')
    GROUP_BY_PARAMS = (('group_by_month', 'month'), ('group_by_nurse', 'nurse'),
                       ('group_by_posting', 'shift_schedule_posting'),
                       ('group_by_can_cover', 'can_cover'))
    ordering_fields = tuple(param[1] for param in GROUP_BY_PARAMS)

    def get_queryset(self):
        return ShiftSchedulePostingResponse.objects.all().select_related('nurse')


class NurseMetrics(generics.GenericAPIView, MetricsMixin):
    """Metrics related to nurses.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    filter_class = NurseFilter

    GROUP_BY_PARAMS = (('group_by_gender', 'gender'),
                       ('group_by_nurse_type', 'nurse_type'))
    FILTER_PARAMS = ('has_fcm_tokens', 'has_messenger_id', 'gender', 'nurse_type', 'min_shifts',)
    ordering_fields = tuple(param[1] for param in GROUP_BY_PARAMS)

    def get_queryset(self):
        return NurseUser.objects.all().prefetch_related('shifts')


class NurseReviewMetrics(generics.GenericAPIView, MetricsMixin):
    """Metrics related to completion of nurse reviews.
    """
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    filter_class = NurseReviewFilter
    serializer_class = NurseReviewSerializer

    FILTER_PARAMS = ('is_public', 'has_rating')
    GROUP_BY_PARAMS = (('group_by_month', 'shift__month'), ('group_by_reservation', 'shift__reservation'), ('group_by_nurse', 'shift__nurse'),)
    ordering_fields = tuple(param[1] for param in GROUP_BY_PARAMS)

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(Review.objects.all())
        if self.request.auth == "ClientUser":
            return queryset.filter(shift__reservation__clientuser=self.request.user).distinct()
        return queryset


class ClientMetrics(generics.GenericAPIView, MetricsMixin):
    """Metrics related to clients.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    filter_class = ClientFilter

    GROUP_BY_PARAMS = (('group_by_reservation_status', 'reservation__status'),)
    FILTER_PARAMS = ('has_fcm_tokens',)
    ordering_fields = tuple(param[1] for param in GROUP_BY_PARAMS)

    def get_queryset(self):
        return ClientUser.objects.all().select_related('reservation')
