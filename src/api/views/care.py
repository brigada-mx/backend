from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.utils import IntegrityError
from django.http import Http404

from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework import status

from database.patients.models import CareLogEntry, NurseCareScheduleTask, CareSchedule
from database.reservations.models import Reservation
from helpers.carelog import task_report
from message.activityfeed.clients import activityfeed_client_carecircle_report
from message.reports import send_carelog_report
from api.serializers import CareLogEntrySerializer, NurseCareScheduleTaskSerializer, CareSendReportSerializer, CareSendReportCareCircleSerializer, CareScheduleCreateUpdateSerializer
from api.filters import CareLogEntryFilter
from api import backends
from api.permissions import HasShiftWithNurseOwner, HasNurseOwner, HasClient
from api.mixins import BooleanParamMixin
from api.helpers import error_response_json



class CareLogEntryList(generics.ListAPIView):
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CareLogEntrySerializer

    filter_class = CareLogEntryFilter
    search_fields = ('additional_instructions', 'additional_observations',)

    def get_queryset(self):
        """Returns a list of all the care log entries assigned to shifts covered by
        the authenticated nurse, or all care log entries if the request comes
        from an admin.
        """
        queryset = self.get_serializer_class().setup_eager_loading(
            CareLogEntry.objects.all().order_by('shift', 'patient', 'shift_day',
                                                'task__end_of_shift', 'time_order',)
        )
        if self.request.auth == "NurseUser":
            queryset = queryset.filter(shift__nurse=self.request.user)
        if self.request.auth == "ClientUser":
            queryset = queryset.filter(shift__reservation__clientuser=self.request.user)
        return queryset


class CareLogEntryDetail(generics.RetrieveUpdateAPIView):
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, HasShiftWithNurseOwner,)
    serializer_class = CareLogEntrySerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(CareLogEntry.objects.all())

    def get_object(self):
        """Nurse can't update care log entry if shift has not started, or if
        more than one `shift_day` has passed since the `shift_day` on which
        `care_log_entry` was scheduled to be performed.

        Overrides `rest_framework.generics.GenericAPIView.get_object`
        """
        UPDATE_LIMIT_DAYS = 3
        obj = get_object_or_404(CareLogEntry, pk=self.kwargs['pk'])
        if self.request.auth is "NurseUser" and self.request.method not in SAFE_METHODS:
            if obj.shift.current_shift_day < 0:
                raise PermissionDenied(
                    error_response_json("This shift for this care log entry has not started yet.",
                                        "No puedes editar la bitácora hasta que empiece el servicio.",))
            if obj.shift.current_shift_day > obj.shift_day + UPDATE_LIMIT_DAYS:
                raise PermissionDenied(
                    error_response_json("Unable to update entry: more than {} day(s) have passed".format(UPDATE_LIMIT_DAYS),
                                        "No puedes editar la bitácora, porque han pasado más de {} días desde el fin del servicio.".format(UPDATE_LIMIT_DAYS),
                                        UPDATE_LIMIT_DAYS,))
        return obj

    def perform_update(self, serializer):
        if serializer.instance.completed is None and 'status' in serializer.validated_data: # ensure that we'll update status
            serializer.instance.completed = timezone.now()
        serializer.save()


class NurseCareScheduleTaskList(generics.ListCreateAPIView, BooleanParamMixin):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication,)
    serializer_class = NurseCareScheduleTaskSerializer

    def filter_is_current(self, request, queryset):
        is_current = request.query_params.get('is_current', None)
        if is_current in self.TRUE_STRINGS:
            return queryset.filter(
                patient__reservation__status__in=(0,1),
                patient__shift_schedules__shiftscheduleday__nurse=request.user).distinct()
        return queryset

    def get_queryset(self):
        """Nurses can read all their `NurseCareScheduleTask`s, even ones that are
        for `ShiftSchedule`s to which they are no longer assigned.
        """
        queryset = self.get_serializer_class().setup_eager_loading(NurseCareScheduleTask.objects.all())
        if self.request.auth == "NurseUser":
            queryset = self.filter_is_current(self.request, queryset.filter(nurse=self.request.user))
        return queryset.order_by('nurse', 'patient', 'task',)

    def create(self, request):
        """Accepts `patient_id` and `nurse_id` params, as opposed to `patient` and
        `nurse`. Nurses can only create `NurseCareScheduleTask`s for their
        patients assigned to recent or upcoming shifts.
        """
        if request.auth != "NurseUser":
            raise PermissionDenied('Only nurse users can create NurseCareScheduleTask instances.')
        try:
            task = NurseCareScheduleTask.objects.create(nurse=request.user, **request.data)
        except IntegrityError as e:
            return Response(error_response_json(str(e), 'Algo salió mal.'), status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer_class()(task, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class CareLogEntryReport(CareLogEntryList):
    def list(self, request, *args, **kwargs):
        entries = self.filter_queryset(self.get_queryset())

        reports_str = request.GET.get('reports')
        reports = reports_str.split(',')

        try:
            report = task_report(entries, reports)
        except AttributeError as e:
            raise ValidationError({'reports': e})

        return Response(report)


class CareLogEntrySendReport(APIView):
    """Sends report to authenticated `ClientUser`.
    """
    authentication_classes = (backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = CareSendReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = Reservation.objects.get(clientuser=request.user)
        min_date = serializer.validated_data['min_date'].isoformat()
        max_date = serializer.validated_data['max_date'].isoformat()
        send_carelog_report.delay(reservation.pk, min_date, max_date, emails=[request.user.email])
        return Response({})


class CareLogEntrySendReportToCareCircle(APIView):
    """Sends report to subset of `CareCircleMember`s, filtered by `contact_type`.
    """
    authentication_classes = (backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = CareSendReportCareCircleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        min_date = serializer.validated_data['min_date'].isoformat()
        max_date = serializer.validated_data['max_date'].isoformat()
        contact_types = serializer.validated_data['contact_types']

        reservation = Reservation.objects.get(clientuser=request.user)
        emails = reservation.carecirclemember_set.filter(contact_type__in=contact_types)\
                                                 .values_list('email', flat=True)
        send_carelog_report.delay(reservation.pk, min_date, max_date, emails=emails)
        activityfeed_client_carecircle_report.delay(request.user.pk)
        return Response({})


class NurseCareScheduleTaskDetail(generics.RetrieveUpdateDestroyAPIView):
    """The only restriction for performing these operations is that nurses must be
    owners of `NurseCareScheduleTask` in order to read or modify them.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, HasNurseOwner,)
    serializer_class = NurseCareScheduleTaskSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(NurseCareScheduleTask.objects.all())


class CareScheduleList(generics.ListCreateAPIView):
    """List and create care schedules.
    """
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CareScheduleCreateUpdateSerializer

    def get_queryset(self):
        queryset = CareSchedule.objects.all()
        if self.request.auth == 'ClientUser':
            queryset = queryset.filter(reservation=self.request.user.reservation)
        return queryset

    def perform_create(self, serializer):
        if not self.request.user.is_client: # only client can create shift schedules via this endpoint
            raise Http404()
        serializer.save(reservation=self.request.user.reservation)


class CareScheduleDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication)
    permission_classes = (permissions.IsAuthenticated, HasClient)
    serializer_class = CareScheduleCreateUpdateSerializer

    def get_queryset(self):
        return CareSchedule.objects.all()
