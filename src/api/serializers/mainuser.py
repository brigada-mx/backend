from rest_framework import serializers

from .base import Serializer


class UserCreateSerializer(Serializer):
    email = serializers.EmailField(allow_blank=False)
    first_name = serializers.CharField(max_length=100, allow_blank=False, trim_whitespace=True)
    surnames = serializers.CharField(max_length=100, allow_blank=False, trim_whitespace=True)


class UserUpdateSerializer(Serializer):
    is_mainuser = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)


class UserReadSerializer(Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    surnames = serializers.CharField()
    is_active = serializers.BooleanField()
