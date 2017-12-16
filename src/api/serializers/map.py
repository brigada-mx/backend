from rest_framework import serializers
from rest_framework.reverse import reverse

from db.map.models import Locality, Organization, Action, ActionLog
from api.mixins import EagerLoadingMixin


class LocalitySerializer(serializers.ModelSerializer):
    meta = serializers.JSONField()

    class Meta:
        model = Locality
        fields = '__all__'


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'


class ActionSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['locality', 'organization']

    locality = LocalitySerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)

    url_log = serializers.SerializerMethodField()

    class Meta:
        model = Action
        fields = '__all__'

    def get_url_log(self, obj):
        return reverse('api:action-log', args=[obj.pk], request=self.context.get('request'))


class ActionLogSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['locality']

    locality = LocalitySerializer(read_only=True)

    class Meta:
        model = ActionLog
        fields = '__all__'
