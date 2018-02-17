from rest_framework import serializers

from api.fields import LatLngField


class LocationSerializer(serializers.Serializer):
    """Converts a param called `location` from a string to a `Point`
    instance, using `LatLngField`.
    """
    location = LatLngField()
