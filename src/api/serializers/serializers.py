from rest_framework import serializers

from api.fields import LatLngField


class DiscourseLoginSerializer(serializers.Serializer):
    sso = serializers.CharField()
    sig = serializers.CharField()
    user_type = serializers.CharField()


class LocationSerializer(serializers.Serializer):
    """Converts a param called `location` from a string to a `Point`
    instance, using `LatLngField`.
    """
    location = LatLngField()


def authenticate(model, email, password):
    if not email or not password:
        return None
    user = model.objects.filter(email=email).first()
    if not user or not user.is_active or not user.check_password(password):
        return None
    return user
