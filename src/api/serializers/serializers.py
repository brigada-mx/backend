from rest_framework import serializers

from db.map.models import AppVersion, EmailNotification
from api.fields import LatLngField


class EagerLoadingMixin:
    @classmethod
    def setup_eager_loading(cls, queryset):
        # foreign key and one to one
        if hasattr(cls, '_SELECT_RELATED_FIELDS'):
            queryset = queryset.select_related(*cls._SELECT_RELATED_FIELDS)
        # many to many, many to one
        if hasattr(cls, '_PREFETCH_RELATED_FIELDS'):
            queryset = queryset.prefetch_related(*cls._PREFETCH_RELATED_FIELDS)
        # each element in this list must be a function that returns a `Prefetch` instance
        if hasattr(cls, '_PREFETCH_FUNCTIONS'):
            queryset = queryset.prefetch_related(*[func() for func in cls._PREFETCH_FUNCTIONS])
        return queryset


class Serializer(serializers.Serializer, EagerLoadingMixin):
    pass


class ModelSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    pass


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
