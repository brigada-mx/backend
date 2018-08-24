from rest_framework.views import APIView
from rest_framework import permissions, generics

from db.users.models import OrganizationUser, DonorUser
from db.map.models import AppVersion, EmailNotification
from api.backends import InternalAuthentication
from api.serializers import OrganizationUserSerializer, DonorUserSerializer, AppVersionSerializer
from api.serializers import EmailNotificationSerializer


class InternalEmailNotificationListCreate(generics.ListCreateAPIView):
    authentication_classes = (InternalAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EmailNotificationSerializer

    def get_queryset(self):
        return EmailNotification.objects.all()


class InternalOrganizationUserList(generics.ListAPIView):
    authentication_classes = (InternalAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = OrganizationUserSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            OrganizationUser.objects.all()
        )


class InternalDonorUserList(generics.ListAPIView):
    authentication_classes = (InternalAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DonorUserSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            DonorUser.objects.all()
        )


class InternalDebugThrowException(APIView):
    """curl -H "Content-Type: application/json" -H "Authorization: Bearer `cat .internal-auth-key`" https://api.brigada.mx/api/internal/debug/throw_exception/
    """
    authentication_classes = (InternalAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        raise Exception('debug')


class InternalAppVersionListCreate(generics.ListCreateAPIView):
    authentication_classes = (InternalAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AppVersionSerializer

    def get_queryset(self):
        return AppVersion.objects.all()
