from rest_framework import serializers

from api.fields import LatLngField


class LocationSerializer(serializers.Serializer):
    """Converts a param called `location` from a string to a `Point`
    instance, using `LatLngField`.
    """
    location = LatLngField()


class SendSetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8, max_length=None, allow_blank=False, trim_whitespace=True)


class PasswordTokenSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8, max_length=None, allow_blank=False, trim_whitespace=True)
    token = serializers.CharField(min_length=20, max_length=None, allow_blank=False, trim_whitespace=True)
