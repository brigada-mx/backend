from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from db.map.models import Action, Organization, Submission
from db.users.models import OrganizationUser, OrganizationUserToken
from api.backends import OrganizationUserAuthentication
from api.serializers import PasswordSerializer, PasswordTokenSerializer
from api.serializers import SendSetPasswordEmailSerializer, OrganizationUserTokenSerializer
from api.serializers import ActionDetailSerializer, SubmissionSerializer, OrganizationMiniSerializer, OrganizationDetailSerializer


class AccountSendSetPasswordEmail(APIView):
    """View for obtaining an auth token by posting a valid email/password tuple.
    """
    throttle_scope = 'authentication'
    serializer_class = SendSetPasswordEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = OrganizationUser.objects.filter(email=email).first()
        if user is not None:
            user.send_set_password_email()
        return Response({'email': email})


class AccountSetPasswordWithToken(APIView):
    """Set org user's password, authenticating with token.
    """
    throttle_scope = 'authentication'
    serializer_class = SendSetPasswordEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = PasswordTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(OrganizationUser, set_password_token=serializer.validated_data['token'])
        user.set_password(serializer.validated_data['password'])
        user.set_password_token = ''
        user.save()
        return Response({'id': user.pk})


class AccountToken(APIView):
    """View for obtaining an auth token by posting a valid email/password tuple.
    """
    throttle_scope = 'authentication'
    serializer_class = OrganizationUserTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = OrganizationUserToken.objects.get_or_create(user=user)
        return Response({'token': token.key, 'id': user.pk})


class AccountSetPassword(APIView):
    """Set org user's password.
    """
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'authentication'
    serializer_class = PasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['password'])
        request.user.save()
        return Response({'id': request.user.pk})


class AccountOrganization(APIView):
    authentication_classes = (OrganizationUserAuthentication,)

    def get(self, request, *args, **kwargs):
        return Response(OrganizationMiniSerializer(self.request.user.organization).data)


class AccountActionListCreate(generics.ListCreateAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    serializer_class = ActionDetailSerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(
            Action.objects.filter(published=True)
        )
        return queryset


class AccountActionDetail(generics.RetrieveUpdateAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    serializer_class = ActionDetailSerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(
            Action.objects.filter(published=True)
        )
        return queryset


class AccountSubmissionDetail(generics.RetrieveUpdateAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(
            Submission.objects.filter(action__published=True)
        )
        return queryset
