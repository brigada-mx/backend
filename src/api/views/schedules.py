from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import Http404

from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication

from database.reservations.models import ShiftSchedule, ShiftScheduleDay, ShiftSchedulePostingResponse
from api.serializers import (
    ShiftScheduleSerializer, ShiftScheduleDaySerializer,
    ShiftSchedulePostingResponseSerializer)
from api import backends
from api.helpers import error_response_json
from api.permissions import HasClient
from message.messengers import notify
from message.notifications import copy
from helpers.datetime import local_date

CREATED_BY_NURSE_CAT = 7


class ShiftScheduleDayList(generics.ListAPIView):
    """List of shift schedule days. For a nurse only days which are current and
    for which they have been assigned are returned.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ShiftScheduleDaySerializer
    ordering_fields = ('shift_schedule', 'day', 'time',)

    def get_queryset(self):
        """Nurses can only see `ShiftScheduleDay`s whose `shift_schedule.end_date`
        isn't more than N days old.
        """
        queryset = ShiftScheduleDay.objects.all()
        if self.request.auth == "NurseUser":
            min_date = local_date(-3)
            return self.get_serializer_class().setup_eager_loading(queryset).filter(
                nurse=self.request.user, shift_schedule__end_date__gte=min_date
            )
        return self.get_serializer_class().setup_eager_loading(queryset)


class ShiftScheduleList(generics.ListCreateAPIView):
    """List and create shift schedules. Not visible to nurses.
    """
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ShiftScheduleSerializer

    def get_queryset(self):
        queryset = ShiftSchedule.objects.all()
        if self.request.auth == 'ClientUser':
            queryset = queryset.filter(reservation=self.request.user.reservation)
        return self.get_serializer_class().setup_eager_loading(queryset)

    def perform_create(self, serializer):
        if not self.request.user.is_client: # only client can create shift schedules via this endpoint
            raise Http404()
        serializer.save(reservation=self.request.user.reservation)


class ShiftScheduleDetail(generics.RetrieveUpdateDestroyAPIView):
    """Shift schedule detail. Not visible to nurses.
    """
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication)
    permission_classes = (permissions.IsAuthenticated, HasClient,)
    serializer_class = ShiftScheduleSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(ShiftSchedule.objects.all())


class ShiftSchedulePostingResponseList(generics.ListAPIView):
    """List of shift schedule posting responses belonging to the authenticated
    nurse.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ShiftSchedulePostingResponseSerializer

    def get_queryset(self):
        """Nurse can only see posting responses for valid postings.
        """
        now = timezone.now()
        queryset = ShiftSchedulePostingResponse.objects.all()
        if self.request.auth == "NurseUser":
            return self.get_serializer_class().setup_eager_loading(queryset).filter(
                nurse=self.request.user,
                shift_schedule_posting__valid_from__lte=now,
                shift_schedule_posting__valid_until__gt=now,
            )
        return self.get_serializer_class().setup_eager_loading(queryset)


class ShiftSchedulePostingRespond(APIView):
    """Respond to a shift schedule posting by updating a
    `ShiftSchedulePostingResponse` instance with the `can_cover` status.

    Only nurse users can hit this endpoint.
    """
    authentication_classes = (backends.NurseTokenAuthentication,)

    def post(self, request, pk, format=None):
        response = get_object_or_404(ShiftSchedulePostingResponse, pk=pk)
        now = timezone.now()
        if request.user != response.nurse or \
        response.shift_schedule_posting.valid_from > now or response.shift_schedule_posting.valid_until < now:
            raise PermissionDenied(
                error_response_json("Schedule not posted for nurse, or schedule not yet/no longer valid.",
                                    "Este servicio ya no está disponible.",))
        # http://stackoverflow.com/questions/28545553/django-rest-frameworks-request-post-vs-request-data
        can_cover = request.data.get('can_cover', 0)
        if response.responded is not None and response.can_cover == can_cover:
            raise PermissionDenied(
                error_response_json("Nurse already responded to this posting.",
                                    "¡Ya pediste cubrir este servicio!",))
        response.respond(can_cover)

        posting, schedule, nurse = (response.shift_schedule_posting,
                                   response.shift_schedule_posting.shift_schedule,
                                   response.nurse)
        notify.delay(
            model="staff",
            messenger="fb_messenger",
            message=copy.NOTIFY_STAFF_POSTING_RESPONSE.format(
                nurse.full_name,
                nurse.pk,
                {0: 'puede cubrir', 1: 'puede cubrir parte de', 2: 'no puede cubrir',}[can_cover],
                schedule.reservation_id,
                schedule.reservation.clientuser_set.first().full_name,
                "{}{}".format(settings.SITE_URL, reverse('staff:jobs:detail', args=[posting.pk])),
            )
        )

        return Response({'responded': response.responded}) # just return responded timestamp
