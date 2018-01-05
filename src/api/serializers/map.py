from rest_framework import serializers
from rest_framework.reverse import reverse

from db.map.models import State, Municipality, Locality, Organization, Action, ActionLog, Establishment
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


class LocalityMiniSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    location = LatLngField()

    class Meta:
        model = Locality
        fields = ('id', 'cvegeo', 'location')


class LocalityMiniWithNameSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    location = LatLngField()

    class Meta:
        model = Locality
        fields = ('id', 'cvegeo', 'location', 'name', 'municipality_name', 'state_name')


class LocalitySerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_RELATED_FIELDS = ['action_set']

    url = serializers.HyperlinkedIdentityField(view_name='api:locality-detail')
    meta = serializers.JSONField()
    location = LatLngField()
    action_count = serializers.SerializerMethodField()
    url_actions = serializers.SerializerMethodField()
    url_establishments = serializers.SerializerMethodField()

    class Meta:
        model = Locality
        fields = '__all__'

    def get_action_count(self, obj):
        return obj.action_set.count()

    def get_url_actions(self, obj):
        return '{}?locality_id={}'.format(
            reverse('api:action-list', request=self.context.get('request')),
            obj.pk
        )

    def get_url_establishments(self, obj):
        return '{}?locality_id={}&is_categorized=true'.format(
            reverse('api:establishment-list', request=self.context.get('request')),
            obj.pk
        )


class LocalityDetailSerializer(LocalitySerializer):
    pass


class ActionLocalitySerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['locality']

    locality = LocalityMiniSerializer(read_only=True)

    class Meta:
        model = Action
        fields = ('id', 'locality', 'action_type', 'budget')


class OrganizationMiniSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    class Meta:
        model = Organization
        fields = '__all__'


class OrganizationSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_RELATED_FIELDS = ['action_set__locality']

    url = serializers.HyperlinkedIdentityField(view_name='api:organization-detail')
    url_actions = serializers.SerializerMethodField()
    actions = ActionLocalitySerializer(source='action_set', many=True, read_only=True)
    action_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = '__all__'

    def get_action_count(self, obj):
        return obj.action_set.count()

    def get_url_actions(self, obj):
        return '{}?organization_id={}'.format(reverse('api:action-list', request=self.context.get('request')), obj.pk)


class EstablishmentSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    location = LatLngField()
    locality = serializers.HyperlinkedRelatedField(view_name='api:locality-detail', read_only=True)
    locality_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Establishment
        fields = '__all__'


class ActionSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['organization']

    url = serializers.HyperlinkedIdentityField(view_name='api:action-detail')
    locality = serializers.HyperlinkedRelatedField(view_name='api:locality-detail', read_only=True)
    locality_id = serializers.IntegerField(read_only=True)
    organization = OrganizationMiniSerializer(read_only=True)
    url_log = serializers.SerializerMethodField()

    class Meta:
        model = Action
        fields = '__all__'

    def get_url_log(self, obj):
        return reverse('api:action-log', args=[obj.pk], request=self.context.get('request'))


class ActionDetailSerializer(ActionSerializer):
    _SELECT_RELATED_FIELDS = ['locality', 'organization']

    locality = LocalityMiniWithNameSerializer(read_only=True)


class OrganizationDetailSerializer(OrganizationSerializer):
    actions = ActionDetailSerializer(source='action_set', many=True, read_only=True)


class ActionLogSerializer(serializers.ModelSerializer, EagerLoadingMixin):

    class Meta:
        model = ActionLog
        fields = '__all__'
