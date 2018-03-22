from rest_framework import permissions, generics

from db.users.models import OrganizationUser
from api.backends import InternalAuthentication
from api.serializers import OrganizationUserSerializer


class InternalOrganizationUserList(generics.ListAPIView):
    authentication_classes = (InternalAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = OrganizationUserSerializer

    def get_queryset(self):
        return OrganizationUser.objects.all()
