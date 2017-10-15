from rest_framework import serializers

from api.fields import LatLngField


class LocationSerializer(serializers.Serializer):
    """Converts a param called `location` from a string to a `Point`
    instance, using `LatLngField`.
    """
    location = LatLngField()


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8, max_length=None, allow_blank=False, trim_whitespace=True)


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=10, max_length=None, allow_blank=False, trim_whitespace=True)
