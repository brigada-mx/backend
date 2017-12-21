from rest_framework import serializers
from rest_framework.reverse import reverse

from db.map.models import State, Municipality, Locality, Organization, Action, ActionLog
from api.mixins import EagerLoadingMixin
from api.fields import LatLngField


class StateSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    meta = serializers.JSONField()

    class Meta:
        model = State
        fields = '__all__'


class MunicipalitySerializer(serializers.ModelSerializer, EagerLoadingMixin):
    meta = serializers.JSONField()

    class Meta:
        model = Municipality
        fields = '__all__'


class LocalitySerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_RELATED_FIELDS = ['action_set']

    url = serializers.HyperlinkedIdentityField(view_name='api:locality-detail')
    meta = serializers.JSONField()
    location = LatLngField()
    action_count = serializers.SerializerMethodField()

    class Meta:
        model = Locality
        fields = '__all__'

    def get_action_count(self, obj):
        return obj.action_set.count()


class ActionSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    url = serializers.HyperlinkedIdentityField(view_name='api:action-detail')
    url_log = serializers.SerializerMethodField()

    class Meta:
        model = Action
        fields = '__all__'

    def get_url_log(self, obj):
        return reverse('api:action-log', args=[obj.pk], request=self.context.get('request'))


class LocalityDetailSerializer(LocalitySerializer):
    actions = ActionSerializer(source='action_set', many=True, read_only=True)


class OrganizationSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    url = serializers.HyperlinkedIdentityField(view_name='api:organization-detail')

    class Meta:
        model = Organization
        fields = '__all__'


class OrganizationDetailSerializer(OrganizationSerializer):
    _PREFETCH_RELATED_FIELDS = ['action_set']
    actions = ActionSerializer(source='action_set', many=True, read_only=True)


class ActionDetailSerializer(ActionSerializer):
    _SELECT_RELATED_FIELDS = ['locality', 'organization']

    locality = LocalitySerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)


class ActionLogSerializer(serializers.ModelSerializer, EagerLoadingMixin):

    class Meta:
        model = ActionLog
        fields = '__all__'
