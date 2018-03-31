from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response

from db.map.models import Donation
from db.users.models import DonorUser, DonorUserToken
from api.backends import DonorUserAuthentication
from api.serializers import PasswordSerializer, PasswordTokenSerializer, SendSetPasswordEmailSerializer
from api.serializers import DonorUserTokenSerializer, DonationSerializer, DonorDonationUpdateSerializer
from api.serializers import DonorUserSerializer, DonorUpdateSerializer, DonorReadSerializer, DonorDonationListSerializer
from api.serializers import DonorDonationCreateSerializer


class DonorSendSetPasswordEmail(APIView):
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = SendSetPasswordEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = DonorUser.objects.filter(email=email).first()
        if user is not None:
            user.send_set_password_email()
        return Response({'email': email})


class DonorSetPasswordWithToken(APIView):
    """Set donor user's password, authenticating with token.
    """
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = PasswordTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(DonorUser, set_password_token=serializer.validated_data['token'])
        if not user.set_password_token_created or user.set_password_token_created < timezone.now() - timedelta(days=3):
            return Response({'error': 'This token has expired'}, status=403)
        user.set_password(serializer.validated_data['password'])
        user.set_password_token = ''
        user.save()
        return Response({'id': user.pk})


class DonorToken(APIView):
    """View for obtaining an auth token by posting a valid email/password tuple.
    """
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = DonorUserTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = DonorUserToken.objects.get_or_create(user=user)
        return Response({'token': token.key, 'id': user.pk, 'donor_id': user.donor.id})


class DonorDeleteToken(APIView):
    authentication_classes = (DonorUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        try:
            token = self.request.user.auth_token
        except ObjectDoesNotExist:
            return Response({}, status=400)
        else:
            token.delete()
            return Response({})


class DonorSetPassword(APIView):
    """Set donor user's password. Requires passing old password for security.
    """
    authentication_classes = (DonorUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({}, status=400)
        request.user.set_password(serializer.validated_data['password'])
        request.user.save()
        return Response({'id': request.user.pk})


class DonorMe(generics.RetrieveUpdateAPIView):
    authentication_classes = (DonorUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DonorUserSerializer

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)


class DonorRetrieveUpdate(generics.RetrieveUpdateAPIView):
    authentication_classes = (DonorUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return DonorUpdateSerializer
        return DonorReadSerializer

    def get_object(self):
        return self.request.user.donor

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)


class DonorDonationListCreate(generics.ListCreateAPIView):
    authentication_classes = (DonorUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return DonorDonationCreateSerializer
        return DonorDonationListSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Donation.objects.filter(donor=self.request.user.donor)
        )

    def perform_create(self, serializer):
        serializer.save(donor=self.request.user.donor, approved_by_donor=True, saved_by='donor')


class DonorDonationRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (DonorUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return DonorDonationUpdateSerializer
        return DonationSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Donation.objects.filter(donor=self.request.user.donor)
        )

    def perform_update(self, serializer):
        serializer.save(saved_by='donor')

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)
