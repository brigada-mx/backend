from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

from rest_framework import permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response

from db.map.models import Donation, Donor
from db.users.models import DonorUser, DonorUserToken
from api.backends import DonorUserAuthentication
from api.serializers import PasswordSerializer, PasswordTokenSerializer, SendSetPasswordEmailSerializer
from api.serializers import DonorUserTokenSerializer, DonationDetailSerializer, DonorDonationUpdateSerializer
from api.serializers import DonorUserSerializer, DonorCreateSerializer, DonorUpdateSerializer, DonorReadSerializer
from api.serializers import DonorDonationCreateSerializer


class DonorDonorCreate(APIView):
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = DonorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        donor_name = serializer.validated_data.pop('donor_name', None)
        donor_id = serializer.validated_data.pop('donor_id', None)
        email = serializer.validated_data['email']
        sector = serializer.validated_data['sector']
        first_name = serializer.validated_data['first_name']
        surnames = serializer.validated_data['surnames']

        try:
            with transaction.atomic():
                if donor_id is not None:  # `donor_id` takes precedence if both are passed
                    donor = get_object_or_404(Donor, id=donor_id)
                    if donor.donoruser_set.first() is not None:
                        return Response({'error': 'This donor already has a user'}, status=400)
                else:
                    donor = Donor.objects.create(name=donor_name)
                donor.sector = sector
                donor.contact = {'email': email, 'person_responsible': f'{first_name} {surnames}'},
                donor.save()
                user = DonorUser.objects.create(
                    donor=donor, email=email, first_name=first_name, surnames=surnames, is_active=False
                )
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        user.send_notify_admin_created_email()
        return Response({})


class DonorSendSetPasswordEmail(APIView):
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = SendSetPasswordEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = DonorUser.objects.filter(email=email).first()
        if user is not None:
            if not user.is_active:
                return Response({'error': 'user not active'})
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
        if serializer.validated_data['created']:
            user.send_training_email()
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
        return DonationDetailSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Donation.objects.filter(donor=self.request.user.donor)
        )

    def perform_create(self, serializer):
        instance = Donation(donor=self.request.user.donor, **serializer.validated_data)
        instance.save(saved_by='donor')
        return Response(serializer.data, status=201)


class DonorDonationRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (DonorUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return DonorDonationUpdateSerializer
        return DonationDetailSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Donation.objects.filter(donor=self.request.user.donor)
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        for attr, value in serializer.validated_data.items():
            setattr(instance, attr, value)
        instance.save(saved_by='donor')

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)
