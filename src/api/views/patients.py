from rest_framework import generics
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response

from database.patients.models import Patient, Address, CareCircleMember
from api.serializers import PatientSerializer, PatientFlatSerializer, PatientDetailSerializer, AddressSerializer, AddressFlatSerializer, CareCircleMemberSerializer, CareCircleNotifySerializer
from api import backends
from api.filters import PatientFilter
from api.permissions import HasClient, HasClientOwner
from message.messengers import notify
from message.activityfeed import activityfeed_client_carecircle_new_member, activityfeed_client_carecircle_notification


class PatientList(generics.ListAPIView):
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PatientSerializer

    filter_class = PatientFilter
    search_fields = ('reservation', 'first_name', 'surname',)

    def get_queryset(self):
        """Returns a list of all the patients assigned to shift_schedules
        covered by the authenticated nurse, or all patients if the request comes
        from an admin.
        """
        queryset = self.get_serializer_class().setup_eager_loading(Patient.objects.all())
        if self.request.auth == "NurseUser":
            return queryset.filter(reservation__status__in=(0,1),
                                   shift_schedules__shiftscheduleday__nurse=self.request.user).distinct()
        if self.request.auth == "ClientUser":
            return queryset.filter(reservation__clientuser=self.request.user).distinct()
        return queryset

    def post(self, request, *args, **kwargs):
        # instantiate create view and pass request and args along to it
        return PatientCreate().dispatch(request, *args, **kwargs)


class PatientCreate(generics.CreateAPIView):
    authentication_classes = (backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, HasClientOwner,)
    serializer_class = PatientDetailSerializer

    def perform_create(self, serializer):
        serializer.save(reservation=self.request.user.reservation)


class PatientDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, HasClient,)
    serializer_class = PatientDetailSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(Patient.objects.all())


class AddressList(generics.ListCreateAPIView):
    authentication_classes = (backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, HasClient,)
    serializer_class = AddressSerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(Address.objects.all())
        if self.request.auth == "ClientUser":
            return queryset.filter(reservation__clientuser=self.request.user).distinct()
        return queryset

    def perform_create(self, serializer):
        serializer.save(reservation=self.request.user.reservation)


class AddressDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, HasClient,)
    serializer_class = AddressSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(Address.objects.all())


class CreateUnauthenticatedMixin(object):
    def perform_create(self, serializer):
        from django.core import signing
        from time import time
        try:
            token = self.request.data.get('token')
            payload = signing.loads(token)
        except Exception as e:
            raise ValidationError({'token_deserialization_error': '{}: {}'.format(e.__class__, e)})

        if payload.get('reservation_id') != serializer.validated_data['reservation'].pk:
            raise ValidationError({'error': 'Incorrect account'})
        if payload.get('expires') < time():
            raise ValidationError({'error': 'Token has expired'})
        if payload.get('namespace') != 'account_create_unauthenticated':
            raise ValidationError({'error': 'Incorrect namespace'})
        return super().perform_create(serializer)

class AddressCreateUnauthenticated(CreateUnauthenticatedMixin, generics.CreateAPIView):
    serializer_class = AddressFlatSerializer
    throttle_scope = 'unauthenticated'

class PatientCreateUnauthenticated(CreateUnauthenticatedMixin, generics.CreateAPIView):
    serializer_class = PatientFlatSerializer
    throttle_scope = 'unauthenticated'


class CareCircleMemberList(generics.ListCreateAPIView):
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, HasClient,)
    serializer_class = CareCircleMemberSerializer

    def get_queryset(self):
        queryset = CareCircleMember.objects.all()
        if self.request.auth == "ClientUser":
            return queryset.filter(reservation__clientuser=self.request.user).distinct()
        return queryset

    def perform_create(self, serializer):
        if not self.request.auth == "ClientUser": # only `ClientUser` can create a client via this endpoint
            raise PermissionDenied()
        instance = serializer.save(reservation=self.request.user.reservation)
        activityfeed_client_carecircle_new_member.delay(pk=instance.pk)


class CareCircleMemberDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, HasClient,)
    serializer_class = CareCircleMemberSerializer

    def get_queryset(self):
        return CareCircleMember.objects.all()


class CareCircleNotify(generics.GenericAPIView):
    authentication_classes = (backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response({'results': CareCircleMember.CONTACT_TYPE_CHOICES})

    def post(self, request, *args, **kwargs):
        reservation = self.request.user.reservation
        contacts = reservation.carecirclemember_set.all()
        serializer = CareCircleNotifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('contact_types'):
            contacts = contacts.filter(contact_type__in=serializer.validated_data.get('contact_types'))

        body = serializer.validated_data.get('body')
        contacts = list(contacts.values_list('pk', flat=True))

        notify.delay(
            model="carecircle",
            recipients=contacts,
            messenger="email",
            context={'body_content': body},
            subject="Mensaje Asistia de {}".format(request.user.full_name),
            body_template='generic_body',
        )
        activityfeed_client_carecircle_notification.delay(pk=reservation.pk, body=body)
        return Response({'contacts_notified': contacts})
