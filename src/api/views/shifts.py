from base64 import b64decode
from sys import maxsize

from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework import status
from rest_framework.permissions import SAFE_METHODS

from database.choices import RELATIONSHIP_CHOICES
from database.reservations.models import Shift, ShiftIncident
from api.serializers import ShiftSerializer, ShiftDetailSerializer, ShiftNurseSubsetSerializer, LocationSerializer, ShiftIncidentSerializer, ShiftSignatureSerializer
from api.filters import ShiftFilter, ShiftIncidentFilter, WITHIN_DAYS_Q
from api import backends
from api.permissions import HasNurseOwner, IsReadableNurseIncidentCategory, HasOwner
from api.mixins import BooleanParamMixin
from api.helpers import error_response_json
from helpers.location import calculate_distance_between_points
from helpers.datetime import timediff
from message.messengers import notify, send_email
from message.notifications import notify_client_checkin, notify_client_checkout

CREATED_BY_NURSE_CAT = 7


class ShiftList(generics.ListAPIView, BooleanParamMixin):
    """List of shifts. For nurses or clients only shifts belonging to given user
    are returned.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ShiftSerializer

    filter_class = ShiftFilter
    search_fields = ('nurse__email', 'nurse__first_name', 'nurse__surname',
                     'patients__first_name', 'patients__surname')
    ordering_fields = ('start',)

    def filter_is_paid(self, request, queryset):
        is_paid = request.query_params.get('is_paid', None)
        if is_paid is not None:
            if is_paid in self.TRUE_STRINGS:
                queryset = queryset.filter(
                    Q(transactions__status="completed") | Q(offline_transactions__status="completed"))
            if is_paid in self.FALSE_STRINGS:
                queryset = queryset.exclude(
                    Q(transactions__status="completed") | Q(offline_transactions__status="completed"))
        return queryset

    def get_queryset(self):
        """Returns a list of all RECENT shifts for the currently authenticated
        nurse, or all shifts if the request comes from an admin.
        """
        queryset = self.get_serializer_class().setup_eager_loading(Shift.objects.all())
        queryset = self.filter_is_paid(self.request, queryset)
        if self.request.auth == "NurseUser":
            queryset = queryset.filter(WITHIN_DAYS_Q(), nurse=self.request.user)
        if self.request.auth == "ClientUser":
            queryset = queryset.filter(reservation__clientuser=self.request.user)
        return queryset


class ShiftUnprotectedList(generics.ListAPIView):
    """List of shifts with a small subset of available fields, but which are not
    restricted to nurses based on their `start` dates.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ShiftNurseSubsetSerializer
    filter_class = ShiftFilter
    ordering_fields = ('start',)

    def get_queryset(self):
        """Returns a list of all shifts for the currently authenticated nurse,
        or all shifts if the request comes from an admin.
        """
        queryset = self.get_serializer_class().setup_eager_loading(Shift.objects.all())
        if self.request.auth == "NurseUser":
            queryset = queryset.filter(nurse=self.request.user)
        return queryset


class ShiftDetail(generics.RetrieveUpdateAPIView):
    """Retrieve details for shift, or update `additional_observations` with a
    PATCH request.

    Serializer includes URLs for shift actions.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication, backends.ClientTokenAuthentication)
    permission_classes = (permissions.IsAuthenticated, HasOwner,)
    serializer_class = ShiftDetailSerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(Shift.objects.all())
        if self.request.auth == "NurseUser":
            if self.request.method not in SAFE_METHODS:
                queryset = queryset.filter(WITHIN_DAYS_Q(lower_days=2, upper_days=0))
            else:
                queryset = queryset.filter(WITHIN_DAYS_Q(lower_days=2))
        return queryset

    def perform_update(self, serializer):
        if self.request.auth == "NurseUser": # NurseUser can only update `additional_observations`
            serializer.instance.additional_observations = serializer.validated_data.get('additional_observations', '')
            serializer.instance.save()
        else:
            serializer.save()


class ShiftAction(APIView):
    """Base view for checking in, checking out, cancelling a shift, creating an
    incident associated with the shift, creating a log entry, etc.

    For the time being, it simplifies things to associate a log entry with just
    a shift, instead of both a shift and a patient.
    """
    _MAX_DISTANCE_METERS = 1000

    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication,)
    queryset = Shift.objects.all()

    def get_object(self, pk):
        shift = get_object_or_404(Shift, pk=pk)
        self.check_object_permissions(self.request, shift) # necessary when overriding `get_object`
        if shift.status is 1: # shift actions can't be invoked on shift cancelled by client
            raise PermissionDenied(
                error_response_json("This shift was cancelled by the client.",
                                    "Este servicio fue cancelado.",))
        return shift

    def action_notify_staff(self, action, shift):
        """Invoke this function within `post` method in instance inheriting
        from this class to `notify` users about action that was performed.

        `shift` must be a Shift instance.
        """
        notify.delay(
            model="staff",
            messenger="fb_messenger",
            message="Acción `{}` en turno `{}` realizada por asociado `{}`.".format(
                action, shift, shift.nurse),
        )

    def check_location(self, shift, request, max_dist=None):
        """Ensure that distance between `Shift` and `location` passed
        in `request` doesn't exceed `max_dist`.
        """
        if max_dist is None:
            max_dist = self._MAX_DISTANCE_METERS
        serializer = LocationSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            distance = calculate_distance_between_points(
                serializer.validated_data.pop('location'),
                shift.address.location,
                meters=True)
            if distance > max_dist:
                raise PermissionDenied(
                    error_response_json("You are not close enough to perform this shift action.",
                                        "Parece que no estás en la ubicación del servicio.\n\nSi crees que esto es un error y estás usando un teléfono Android, haz lo siguiente:\n1. Abre Google Maps y checa tu ubcación allí\n2. Regresa a la aplicación y recarga los datos del turno\n3. Intenta hacer la acción otra vez",
                                        distance, 'location',))

    def check_time(self, time=None, reference=None, lb=-maxsize, ub=maxsize):
        """Ensure that time difference between two `DateTime` instances, `time`
        and `reference`, is within the lower `lb` and the upper `ub`.
        """
        time_diff = timediff(t1=time or timezone.now(), t0=reference or timezone.now(), fmt='h')
        if not lb <= time_diff <= ub: # interval comparison =)
            raise PermissionDenied(
                error_response_json("It is either too early or too late to perform this shift action.",
                                    "Parece que es demasiado temprano o demasiado tarde para hacer esta acción.",
                                    time_diff, 'time',))


class ShiftCancel(ShiftAction):
    """View for nurse to update shift's assigned nurse to `None`,
    if nurse is "owner" of shift.
    """
    permission_classes = (permissions.IsAuthenticated, HasNurseOwner,)

    def post(self, request, pk, format=None):
        shift = self.get_object(pk)
        if shift.checkin is not None:
            raise PermissionDenied(
                error_response_json("You have already checked in to this shift, you can't cancel it now.",
                                    "Ya se marcó tu entrada a este servicio, no lo puedes cancelar.",))
        self.action_notify_staff("cancel", shift)
        ShiftIncident(shift=shift, nurse=shift.nurse, category=1).save()
        shift.nurse = None # ShiftIncident post_save signal also takes care of this
        shift.save()
        assert shift.status == 0, '`shift.status` should still be `active` if nurse cancels shift'
        return Response(ShiftSerializer(shift, context={'request': request}).data)


class ShiftCheckin(ShiftAction):
    """Location and timestamp are validated. `checkin` must be `None`.
    """
    permission_classes = (permissions.IsAuthenticated, HasNurseOwner,)

    def post(self, request, pk, format=None):
        shift = self.get_object(pk)
        if shift.checkin is not None:
            raise PermissionDenied(
                error_response_json("You have already checked in to this shift.",
                                    "Ya se marcó tu entrada a este servicio.",))
        now = timezone.now()
        self.check_time(now, shift.start, -6, 12)
        self.check_location(shift, request)
        shift.checkin = now
        shift.save()
        self.action_notify_staff("checkin", shift)
        notify_client_checkin.delay(shift.pk)
        return Response(ShiftSerializer(shift, context={'request': request}).data)


class ShiftCheckout(ShiftAction):
    """Location and timestamp are validated. `checkin` must not be `None`,
    and `checkout` must be `None`.
    """
    permission_classes = (permissions.IsAuthenticated, HasNurseOwner,)

    def post(self, request, pk, format=None):
        shift = self.get_object(pk)
        if shift.checkin is None:
            raise PermissionDenied(
                error_response_json("You haven't checked in to this shift yet.",
                                    "¡No puedes marcar tu salida porque todavía no has marcado tu entrada!",))
        if shift.checkout is not None:
            raise PermissionDenied(
                error_response_json("You have already checked out of this shift.",
                                    "Ya marcaste tu salida de este servicio... ¡Todo bien!",))
        now = timezone.now()
        self.check_time(now, shift.end, -6, 12)
        shift.checkout = now
        shift.save()
        self.action_notify_staff("checkout", shift)
        notify_client_checkout.delay(shift.pk)
        return Response(ShiftSerializer(shift, context={'request': request}).data)


class ShiftIncidentCreate(ShiftAction, generics.CreateAPIView):
    """View to create a `ShiftIncident` instance. Category can
    only be set by admin user.
    """
    permission_classes = (permissions.IsAuthenticated, HasNurseOwner,)
    serializer_class = ShiftIncidentSerializer

    def post(self, request, pk, format=None):
        shift = self.get_object(pk) # method inherited from `ShiftAction`
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            if request.auth == "NurseUser":
                now = timezone.now()
                self.check_time(now, shift.start, -3, None) # not more than X hours before start of shift
                self.check_time(now, shift.end, None, 12) # not more than Y hours after end of shift
                serializer.save(shift=shift, category=CREATED_BY_NURSE_CAT)
                self.action_notify_staff("incident", shift)
            else:
                serializer.save(shift=shift)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShiftIncidentDetail(generics.RetrieveUpdateAPIView):
    """View to retrieve or update a `ShiftIncident` instance. Category can only
    be set by admin user.

    Incidents with certain categories are not visible to nurses. Also, only
    incidents created by nurses can be updated by nurses, and nurses can't
    update the `category` of these instances.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, HasNurseOwner, IsReadableNurseIncidentCategory,)
    queryset = ShiftIncident.objects.all()
    serializer_class = ShiftIncidentSerializer

    def perform_update(self, serializer):
        if self.request.auth == "NurseUser":
            incident = self.get_object()
            if incident.category is not CREATED_BY_NURSE_CAT:
                return
            serializer.save(category=CREATED_BY_NURSE_CAT)
        else:
            serializer.save()


class ShiftIncidentList(generics.ListAPIView):
    """List of shift incidents. For nurse user only incidents belonging to nurse
    user are returned.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ShiftIncidentSerializer

    filter_class = ShiftIncidentFilter
    search_fields = ('description', 'solution',)
    ordering_fields = ('created',)

    def get_queryset(self):
        """Returns a list of all the shift incidents for the currently
        authenticated nurse, or all if the request comes from an admin.
        """
        if self.request.auth == "NurseUser":
            return self.get_serializer_class().setup_eager_loading(
                ShiftIncident.objects.for_nurse_user().filter(nurse=self.request.user)
            )
        return self.get_serializer_class().setup_eager_loading(ShiftIncident.objects.all())


class ShiftSignatureUpload(generics.CreateAPIView):
    """View to upload a Shift signature."""
    permission_classes = (permissions.IsAuthenticated, HasNurseOwner,)
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication,)
    serializer_class = ShiftSignatureSerializer

    def get(self, request, *args, **kwargs):
        return Response({'results': RELATIONSHIP_CHOICES})

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            shift = get_object_or_404(Shift, pk=kwargs.get('pk'))
            signature_encoded = serializer.validated_data.get('signature').split(',')[1]
            signature_decoded = b64decode(signature_encoded)
            try:
                serializer.save(
                    shift=shift,
                    signature=ContentFile(signature_decoded, 'signature.png'))
            except IntegrityError:
                raise PermissionDenied(error_response_json(
                    'This shift has been already signed.',
                    'Este shift ya ha sido firmado.'))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShiftRequestSignature(APIView):
    """View for sending signature request email to the Shift client."""
    permission_classes = (permissions.IsAuthenticated, HasNurseOwner,)
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication,)

    def get(self, request, *args, **kwargs):
        shift = get_object_or_404(Shift, pk=kwargs.get('pk'))

        if shift.get_signature():
            raise PermissionDenied(error_response_json(
                'This shift has been already signed.',
                'Este shift ya ha sido firmado.'))

        log_url = "{}{}".format(
            settings.SITE_URL,
            reverse('reservations:shift-signature', kwargs={
                'shift_hashed_id': shift.hashed_id,
                'rhpk': shift.reservation.signup_token
            }))
        log_signature = render_to_string(
            'reservations/email/log_signature.html',
            {'shift': shift, 'log_url': log_url})
        context = {'body_content': log_signature}

        send_email.delay(
            recipients=shift.reservation.get_client_email(),
            subject='Bitácora y Firma del Servicio {}'.format(shift.public_id),
            body_template='generic_body',
            context=context
        )
        return Response()
