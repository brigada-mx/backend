from rest_framework import permissions, generics
from rest_framework.serializers import ValidationError

from db.users.models import DonorUser, OrganizationUser
from api.backends import OrganizationUserAuthentication, DonorUserAuthentication
from api.serializers import UserCreateSerializer, UserUpdateSerializer, UserReadSerializer


class IsMainUser(permissions.BasePermission):
    def has_permission(self, request, view, obj):
        # read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_mainuser


class OrganizationUserListCreate(generics.ListCreateAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsMainUser)
    throttle_scope = 'authentication'

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserReadSerializer

    def get_queryset(self):
        return OrganizationUser.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class OrganizationUserRetrieveUpdate(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsMainUser)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer
        return UserReadSerializer

    def get_queryset(self):
        return OrganizationUser.objects.filter(organization=self.request.user.organization)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.id == request.user.id:
            raise ValidationError(f"User can't deactivate or demote itself")
        return self.patch(request, *args, **kwargs)


class DonorUserListCreate(generics.ListCreateAPIView):
    authentication_classes = (DonorUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsMainUser)
    throttle_scope = 'authentication'

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserReadSerializer

    def get_queryset(self):
        return DonorUser.objects.filter(donor=self.request.user.donor)

    def perform_create(self, serializer):
        serializer.save(donor=self.request.user.donor)


class DonorUserRetrieveUpdate(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (DonorUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsMainUser)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer
        return UserReadSerializer

    def get_queryset(self):
        return DonorUser.objects.filter(donor=self.request.user.donor)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.id == request.user.id:
            raise ValidationError(f"User can't deactivate or demote itself")
        return self.patch(request, *args, **kwargs)
