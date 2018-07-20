from rest_framework import serializers

from db.users.models import OrganizationUser, DonorUser
from .base import Serializer, ModelSerializer


class OrganizationUserCreateSerializer(ModelSerializer):
    class Meta:
        model = OrganizationUser
        fields = ('email', 'first_name', 'surnames')


class DonorUserCreateSerializer(ModelSerializer):
    class Meta:
        model = OrganizationUser
        fields = ('email', 'first_name', 'surnames')


class OrganizationUserUpdateSerializer(ModelSerializer):
    class Meta:
        model = OrganizationUser
        fields = ('is_mainuser', 'is_active')


class DonorUserUpdateSerializer(ModelSerializer):
    class Meta:
        model = DonorUser
        fields = ('is_mainuser', 'is_active')


class UserReadSerializer(Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    surnames = serializers.CharField()
    is_active = serializers.BooleanField()
    is_mainuser = serializers.BooleanField()
