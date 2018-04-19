from rest_framework import permissions, generics

from db.users.models import OrganizationUser, DonorUser
from db.map.models import AppVersion
from api.backends import InternalAuthentication
from api.serializers import OrganizationUserSerializer, DonorUserSerializer, AppVersionSerializer


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


class AppVersionListCreate(generics.ListCreateAPIView):
    authentication_classes = (InternalAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AppVersionSerializer

    def get_queryset(self):
        return AppVersion.objects.all()
