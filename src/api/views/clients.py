import binascii
import os

from django.db import transaction

from rest_framework.response import Response
from rest_framework import parsers, renderers
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied

from database.clients.models import ClientUser, ActivityFeedItem
from database.reservations.models import Reservation
from message.messengers import notify
from api.models import ClientUserToken
from api.serializers import ClientUserSerializer, ClientUserDetailSerializer, ClientUserAuthTokenSerializer, ClientSendPasswordEmailSerializer, PasswordSerializer, ClientCreateUserSerializer, ClientCardsSerializer, ActivityFeedItemSerializer
from api import backends
from api.permissions import IsClientUser, HasClientOwner
from api.mixins import AddRemoveFCMTokenMixin
from api.filters import ActivityFeedItemFilter


class ObtainClientAuthToken(APIView):
    """View for obtaining an auth token by posting a valid email/password tuple.
    """
    throttle_scope = 'authentication'
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = ClientUserAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = ClientUserToken.objects.get_or_create(user=user)
        return Response({'token': token.key, 'pk': user.pk, 'full_name': user.full_name, 'email': user.email})


class ClientSendSetPasswordEmail(APIView):
    """View for saving `set_password_code` on client and sending email to client
    with `set_password_code` embedded in link.
    """
    authentication_classes = (backends.ClientTokenAuthentication,) # user doesn't have to be authenticated to hit this endpoint

    def post(self, request, *args, **kwargs):
        serializer = ClientSendPasswordEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        email_type = serializer.validated_data['email_type']

        client = ClientUser.objects.filter(email=email).first()
        if not client:
            return Response(status=status.HTTP_404_NOT_FOUND)

        client.set_password_code = binascii.hexlify(os.urandom(20)).decode()
        client.save()

        invited_by = None
        if self.request.auth == "ClientUser":
            invited_by = self.request.user.full_name

        context = {
            'email': email,
            'set_password_link': reverse('api:set-password-form', request=request,
                kwargs={'user_type': 'clients', 'code': client.set_password_code}
            ),
            'email_type': email_type,
            'invited_by': invited_by,
            'patient_names': client.reservation.get_patient_names(),
        }
        invited_subject = '{} te ha invitado a formar parte de su cuenta Asistia'.format(invited_by)

        notify.delay(
            model="client",
            recipients=client.pk,
            messenger="email",
            context=context,
            subject={
                'create': 'Activa tu Cuenta Asistia',
                'create_admin': 'Baja aplicación Asistia y Activa Tu Cuenta',
                'reset': 'Restablece tu Contraseña Asistia',
                'invite_carecircle': invited_subject,
                'invite_client': invited_subject,
            }[email_type],
            body_template='client_set_password',
        )
        return Response({'email': email})


class ClientSetPassword(APIView):
    """Set client's password.
    """
    authentication_classes = (backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        request.user.set_password(password); request.user.save()
        return Response({'id': request.user.pk})


class ClientCreateUserAccount(APIView):
    """Create reservation and user, and assign user to newly created reservation.
    Don't create anything if user with this email already exists.
    """

    def post(self, request, *args, **kwargs):
        serializer = ClientCreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if ClientUser.objects.filter(email=serializer.validated_data['email']).first():
            return Response({'error': 'A user with this email already exists', 'type': 'email_exists'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            reservation = Reservation.objects.create(status=0, by_admin=False)
            user = ClientUser.objects.create(reservation=reservation, account_holder=True, **serializer.validated_data)

        notify.delay(
            model='staff',
            messenger='email',
            context={'body_content': '{}, acaba de usar la aplicación Asistia para crear una nueva cuenta.\n\nSu email es {}, y su teléfono es {}.'.format(user.full_name, user.email, user.phone)},
            subject='Nuevo Cliente desde Aplicación',
            body_template='generic_body',
        )
        return Response({'id': user.pk, 'reservation_id': reservation.pk, 'token': self.create_token(reservation)})

    def create_token(self, reservation):
        """Used in `CreateUnauthenticatedMixin`.
        """
        from django.core import signing
        from time import time
        return signing.dumps({'reservation_id': reservation.pk,
                              'expires': time()+3600*2,
                              'namespace': 'account_create_unauthenticated',})


class ClientList(generics.ListCreateAPIView):
    """List clients or create a client.
    """
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ClientUserSerializer

    search_fields = ('email', 'first_name', 'surname',)

    def get_queryset(self):
        """Returns a list of clients, or info for the client user making the request.
        """
        queryset = self.get_serializer_class().setup_eager_loading(ClientUser.objects.all())
        if self.request.auth == "ClientUser":
            return queryset.filter(reservation__clientuser=self.request.user).distinct()
        return queryset

    def perform_create(self, serializer):
        if not self.request.auth == "ClientUser": # only `ClientUser` can create a client via this endpoint
            raise PermissionDenied()
        serializer.save(reservation=self.request.user.reservation, account_holder=None)


class ClientDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve details for client, or update client.
    """
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsClientUser,)
    queryset = ClientUser.objects.all()
    serializer_class = ClientUserDetailSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(ClientUser.objects.all())


class ClientAddFCMToken(APIView, AddRemoveFCMTokenMixin):
    """Add an FCM token to the client's list of tokens.
    """
    authentication_classes = (backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        return self.add_token(request, *args, **kwargs)


class ClientRemoveFCMToken(ClientAddFCMToken):
    """Remove an FCM token from the client's list of tokens.
    """
    def post(self, request, *args, **kwargs):
        return self.remove_token(request, *args, **kwargs)


class ClientChangeAccountHolder(generics.GenericAPIView):
    """Create reservation and user, and assign user to newly created reservation.
    Don't create anything if user with this email already exists.
    """
    authentication_classes = (backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, HasClientOwner,)
    queryset = ClientUser.objects.all()

    def post(self, request, *args, **kwargs):
        owner = request.user
        client = self.get_object()
        with transaction.atomic():
            owner.account_holder = None
            owner.save()
            client.account_holder = True
            client.save()
        return Response(ClientUserSerializer(client, context={'request': request}).data)


class ClientAddCards(generics.GenericAPIView):
    queryset = ClientUser.objects.all()

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = ClientCardsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client = self.get_object()
        serializer.save(client=client)
        return Response(serializer.data)


class ActivityFeedItemList(generics.ListAPIView):
    """List of `ActivityFeedItem`s. For clients only items belonging to their
    account are returned.
    """
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ActivityFeedItemSerializer

    filter_class = ActivityFeedItemFilter
    search_fields = ('title', 'body',)
    ordering_fields = ('date',)

    def get_queryset(self):
        queryset = ActivityFeedItem.objects.all()
        if self.request.auth == "ClientUser":
            queryset = queryset.filter(reservation__clientuser=self.request.user)
        return queryset
