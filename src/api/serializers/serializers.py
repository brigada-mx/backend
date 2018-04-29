from rest_framework import serializers

from db.map.models import AppVersion, EmailNotification
from api.fields import LatLngField


class EmailNotificationSerializer(serializers.ModelSerializer):
    args = serializers.JSONField()

    class Meta:
        model = EmailNotification
        fields = '__all__'


class AppVersionSerializer(serializers.ModelSerializer):
    git_hash_short = serializers.ReadOnlyField()

    class Meta:
        model = AppVersion
        fields = '__all__'


class DiscourseLoginSerializer(serializers.Serializer):
    sso = serializers.CharField()
    sig = serializers.CharField()


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
