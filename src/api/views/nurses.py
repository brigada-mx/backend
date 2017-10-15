from time import time
import binascii
import os

from django.db import transaction
from django.core import signing
from rest_framework.response import Response
from rest_framework import parsers, renderers
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.reverse import reverse

from database.nurses.models import NurseUser, Review
from message.messengers import notify
from api.models import NurseUserToken
from api.serializers import NurseUserSerializer, NurseUserDetailSerializer, NurseUserAuthTokenSerializer, NurseUserCreateSerializer, NurseSendPasswordEmailSerializer
from api import backends
from api.permissions import IsNurseUser
from api.mixins import AddRemoveFCMTokenMixin
from api.filters import NurseFilter
from api.filters import NurseReviewFilter
from api.serializers import NurseReviewSerializer
from api.helpers import error_response_json


class ObtainNurseAuthToken(APIView):
    """View for obtaining an auth token by posting a valid
    email/phone tuple.
    """
    throttle_scope = 'authentication'
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = NurseUserAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = NurseUserToken.objects.get_or_create(user=user)
        return Response({'token': token.key, 'pk': user.pk, 'full_name': user.full_name,
                         'email': user.email, 'messenger_id': user.messenger_id,})


class NurseSendSetPasswordEmail(APIView):
    """View for saving `set_password_code` on nurse and sending email to nurse
    with `set_password_code` embedded in link.
    """
    def post(self, request, *args, **kwargs):
        serializer = NurseSendPasswordEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        email_type = serializer.validated_data['email_type']

        nurse = NurseUser.objects.filter(email=email).first()
        if not nurse:
            return Response(status=status.HTTP_404_NOT_FOUND)

        nurse.set_password_code = binascii.hexlify(os.urandom(20)).decode()
        nurse.save()

        context = {
            'email': email,
            'set_password_link': reverse('api:set-password-form', request=request,
                kwargs={'user_type': 'nurses', 'code': nurse.set_password_code}
            ),
            'email_type': email_type,
        }

        notify.delay(
            model="nurse",
            recipients=nurse.pk,
            messenger="email",
            context=context,
            subject={
                'create': 'Activa tu Cuenta Asistia',
                'create_admin': 'Baja aplicación Asistia y Activa Tu Cuenta',
                'reset': 'Restablece tu Contraseña Asistia',
            }[email_type],
            body_template='nurse_set_password',
        )
        return Response({'email': email})


class NurseAddFCMToken(APIView, AddRemoveFCMTokenMixin):
    """Add an FCM token to the nurse's list of tokens.
    """
    authentication_classes = (backends.NurseTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        return self.add_token(request, *args, **kwargs)


class NurseRemoveFCMToken(NurseAddFCMToken):
    """Remove an FCM token from the nurse's list of tokens.
    """
    def post(self, request, *args, **kwargs):
        return self.remove_token(request, *args, **kwargs)


class NurseList(generics.ListAPIView):
    """List of nurses.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication, backends.ClientTokenAuthentication,backends.InternalAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NurseUserSerializer
    filter_class = NurseFilter

    search_fields = ('email', 'first_name', 'surname',)

    def get_queryset(self):
        """Returns a list of nurses, or info for the nurse user making the request.
        """
        queryset = self.get_serializer_class().setup_eager_loading(NurseUser.objects.all())
        if self.request.auth == "NurseUser":
            return queryset.filter(pk=self.request.user.pk).distinct()
        if self.request.auth == "ClientUser": # only return nurses assigned connected to clients' reservations
            return queryset.filter(
                shifts__reservation=self.request.user.reservation,
            ).distinct()
        return queryset.distinct()


class NurseUserCreate(APIView):
    """Create nurse user. Don't create anything if nurse user with this email
    already exists.
    """
    def post(self, request, *args, **kwargs):
        serializer = NurseUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        if NurseUser.objects.filter(email=email).first():
            return Response({'error': 'A nurse with this email already exists', 'type': 'email_exists'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            nurse = NurseUser.objects.create(**serializer.validated_data)
            nurse.set_password(password)
            nurse.save()

        response = NurseUserCreateSerializer(nurse, context={'request': request}).data
        response.update({'id': nurse.pk, 'token': self.create_token(nurse)})
        return Response(response)

    def create_token(self, nurse):
        """Used in `UpdateUnauthenticatedMixin`.
        """
        return signing.dumps({'nurse_id': nurse.pk,
                              'expires': time()+3600*2,
                              'namespace': 'update_nurse_unauthenticated',})


class NurseDetail(generics.RetrieveUpdateAPIView):
    """Retrieve details for nurse, or update nurse.
    """
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication, backends.UnauthenticatedNurse)
    permission_classes = (permissions.IsAuthenticated, IsNurseUser,)
    serializer_class = NurseUserDetailSerializer

    def get_queryset(self):
        qs = NurseUser.objects.all()
        if self.request.auth == 'NurseUser':
            qs = qs.filter(id=self.request.user.id)
        return self.get_serializer_class().setup_eager_loading(qs)

class NurseReviewList(generics.ListAPIView):
    """List nurse reviews.
    """
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NurseReviewSerializer
    filter_class = NurseReviewFilter

    ordering_fields = ('date',)

    def get_queryset(self):
        """Returns a list of reviews for the authenticated client's account.
        """
        queryset = self.get_serializer_class().setup_eager_loading(Review.objects.all())
        if self.request.auth == "ClientUser":
            return queryset.filter(shift__reservation__clientuser=self.request.user).distinct()
        return queryset


class NurseReviewDetail(generics.RetrieveUpdateAPIView):
    """Read or update nurse review.
    """
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NurseReviewSerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(Review.objects.all())
        if self.request.auth == "ClientUser":
            return queryset.filter(shift__reservation__clientuser=self.request.user).distinct()
        return queryset

    def update(self, request, *args, **kwargs):
        """Client can't complete reviews that are more than N days old, and can't
        update already completed reviews that are more than M days old, where M is
        at most a few days.
        """
        instance = self.get_object()
        if instance.is_expired:
            raise PermissionDenied(
                error_response_json('Too much time has passed to complete this review.', 'Ha pasado demasiado tiempo para completar esta reseña.', error_type='is_expired'))
        if instance.is_completed:
            raise PermissionDenied(
                error_response_json('This review has already been completed.', 'Ya se completó esta reseña.', error_type='  is_completed'))
        return super().update(request, *args, **kwargs)
