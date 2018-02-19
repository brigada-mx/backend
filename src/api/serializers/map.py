from django.db.models import Prefetch

from rest_framework import serializers

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


class LocalitySearchSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    location = LatLngField()

    class Meta:
        model = Locality
        fields = ('id', 'cvegeo', 'location', 'name', 'municipality_name', 'state_name')


class LocalityRawSerializer(serializers.ModelSerializer):
    meta = serializers.SerializerMethodField()
    location = LatLngField()
    action_count = serializers.SerializerMethodField()

    class Meta:
        model = Locality
        fields = ('id', 'cvegeo', 'cvegeo_municipality', 'cvegeo_state', 'name', 'municipality_name',
                  'state_name', 'location', 'meta', 'action_count')

    def get_meta(self, obj):
        keys = ['destroyed', 'habit', 'margGrade', 'notHabit', 'total']
        return {key: obj.meta.get(key) for key in keys}

    def get_action_count(self, obj):
        return obj.action_count


class LocalityDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_RELATED_FIELDS = ['action_set']

    meta = serializers.JSONField()
    location = LatLngField()
    action_count = serializers.SerializerMethodField()

    class Meta:
        model = Locality
        fields = '__all__'

    def get_action_count(self, obj):
        return obj.action_set.filter(published=True).count()


class ActionSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    url = serializers.HyperlinkedIdentityField(view_name='api:action-detail')
    locality = serializers.HyperlinkedRelatedField(view_name='api:locality-detail', read_only=True)
    locality_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Action
        fields = '__all__'


class SubmissionMediumSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    data = serializers.SerializerMethodField()
    image_urls = serializers.SerializerMethodField()
    thumbnails_small = serializers.SerializerMethodField()
    thumbnails_medium = serializers.SerializerMethodField()
    location = LatLngField()
    description = serializers.ReadOnlyField()
    address = serializers.ReadOnlyField()

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


class SubmissionSerializer(SubmissionMediumSerializer):
    _SELECT_RELATED_FIELDS = ['action']

    action = ActionSerializer(read_only=True)


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
    _PREFETCH_FUNCTIONS = [
        lambda: Prefetch('action_set', queryset=Action.objects.select_related('locality').prefetch_related(
            Prefetch('submission_set', queryset=Submission.objects.filter(published=True))
        ).filter(published=True))
    ]

    url = serializers.HyperlinkedIdentityField(view_name='api:organization-detail')
    actions = ActionLocalitySerializer(source='action_set', many=True, read_only=True)
    action_count = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        exclude = ('secret_key',)

    def get_action_count(self, obj):
        return obj.action_set.all().count()

    def get_image_count(self, obj):
        actions = obj.action_set.all()
        return sum(
            sum(len(s.synced_image_urls()) for s in a.submission_set.all()) for a in actions
        )


class EstablishmentSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    location = LatLngField()
    locality = serializers.HyperlinkedRelatedField(view_name='api:locality-detail', read_only=True)
    locality_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Establishment
        fields = '__all__'


class ActionDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [lambda: Prefetch('submission_set', queryset=Submission.objects.filter(published=True))]
    _SELECT_RELATED_FIELDS = ['locality', 'organization']

    locality = LocalityMediumSerializer(read_only=True)
    organization = OrganizationMiniSerializer(read_only=True)
    submissions = SubmissionMediumSerializer(source='submission_set', many=True, read_only=True)

    class Meta:
        model = Action
        fields = '__all__'


class ActionSubmissionsSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [lambda: Prefetch('submission_set', queryset=Submission.objects.filter(published=True))]
    _SELECT_RELATED_FIELDS = ['locality', 'organization']

    locality = LocalityMediumSerializer(read_only=True)
    organization = OrganizationMiniSerializer(read_only=True)
    submissions = SubmissionMiniSerializer(source='submission_set', many=True, read_only=True)
    first_thumbnail_medium = serializers.SerializerMethodField()

    class Meta:
        model = Action
        fields = '__all__'

    def get_first_thumbnail_medium(self, obj):
        try:
            return obj.submission_set.first().thumbnails(1280, 240, crop=True)[0]
        except:
            return None


class OrganizationDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [
        lambda: Prefetch('action_set', queryset=Action.objects.select_related(
            'locality', 'organization'
        ).prefetch_related(
            Prefetch('submission_set', queryset=Submission.objects.filter(published=True))
        ).filter(published=True))
    ]

    actions = ActionSubmissionsSerializer(source='action_set', many=True, read_only=True)
    action_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        exclude = ('secret_key',)

    def get_action_count(self, obj):
        return obj.action_set.all().count()


class ActionLogSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    class Meta:
        model = ActionLog
        fields = '__all__'
