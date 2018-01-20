from rest_framework import serializers
from rest_framework.reverse import reverse

from db.map.models import State, Municipality, Locality, Establishment
from db.map.models import Organization, Action, ActionLog, Submission
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


class LocalityMediumSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    location = LatLngField()

    class Meta:
        model = Locality
        fields = ('id', 'cvegeo', 'location', 'name', 'municipality_name', 'state_name', 'meta')


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
        return obj.action_set(manager='public_objects').count()

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


class ActionSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    url = serializers.HyperlinkedIdentityField(view_name='api:action-detail')
    locality = serializers.HyperlinkedRelatedField(view_name='api:locality-detail', read_only=True)
    locality_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Action
        fields = '__all__'


class SubmissionSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['action']

    data = serializers.SerializerMethodField()
    image_urls = serializers.SerializerMethodField()
    thumbnails_small = serializers.SerializerMethodField()
    thumbnails_medium = serializers.SerializerMethodField()
    location = LatLngField()
    action = ActionSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = '__all__'

    def get_data(self, obj):
        data = obj.data
        data.pop('org_key', None)
        return data

    def get_image_urls(self, obj):
        return obj.synced_image_urls()

    def get_thumbnails_small(self, obj):
        return obj.thumbnails(240, 240, crop=True)

    def get_thumbnails_medium(self, obj):
        return obj.thumbnails(1280, 1280)


class SubmissionMiniSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    thumbnails_small = serializers.SerializerMethodField()
    location = LatLngField()

    class Meta:
        model = Submission
        fields = ('id', 'thumbnails_small', 'location')

    def get_thumbnails_small(self, obj):
        return obj.thumbnails(240, 240, crop=True)


class ActionLocalitySerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['locality']

    locality = LocalityMiniSerializer(read_only=True)

    class Meta:
        model = Action
        fields = ('id', 'locality', 'action_type', 'budget')


class OrganizationMiniSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    class Meta:
        model = Organization
        exclude = ('secret_key',)


class OrganizationSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_RELATED_FIELDS = ['action_set__locality']

    url = serializers.HyperlinkedIdentityField(view_name='api:organization-detail')
    url_actions = serializers.SerializerMethodField()
    actions = ActionLocalitySerializer(source='action_set', many=True, read_only=True)
    action_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        exclude = ('secret_key',)

    def get_action_count(self, obj):
        return obj.action_set(manager='public_objects').count()

    def get_url_actions(self, obj):
        return '{}?organization_id={}'.format(reverse('api:action-list', request=self.context.get('request')), obj.pk)


class EstablishmentSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    location = LatLngField()
    locality = serializers.HyperlinkedRelatedField(view_name='api:locality-detail', read_only=True)
    locality_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Establishment
        fields = '__all__'


class ActionDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['locality', 'organization']
    _PREFETCH_RELATED_FIELDS = ['submission_set']

    locality = LocalityMediumSerializer(read_only=True)
    organization = OrganizationMiniSerializer(read_only=True)
    submissions = SubmissionSerializer(source='submission_set', many=True, read_only=True)

    class Meta:
        model = Action
        fields = '__all__'


class ActionSubmissionsSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['locality', 'organization']
    _PREFETCH_RELATED_FIELDS = ['submission_set']

    locality = LocalityMediumSerializer(read_only=True)
    organization = OrganizationMiniSerializer(read_only=True)
    submissions = SubmissionMiniSerializer(source='submission_set', many=True, read_only=True)

    class Meta:
        model = Action
        fields = '__all__'


class OrganizationDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_RELATED_FIELDS = ['action_set__submission_set', 'action_set__locality', 'action_set__organization']

    actions = ActionSubmissionsSerializer(source='action_set', many=True, read_only=True)
    action_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        exclude = ('secret_key',)

    def get_action_count(self, obj):
        return obj.action_set(manager='public_objects').count()


class ActionLogSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    class Meta:
        model = ActionLog
        fields = '__all__'
