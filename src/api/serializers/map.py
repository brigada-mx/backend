from django.db.models import Prefetch

from rest_framework import serializers

from db.map.models import State, Municipality, Locality, Establishment, VolunteerOpportunity, VolunteerApplication
from db.map.models import Organization, Action, ActionLog, Submission, Donor, Donation
from db.users.models import DonorUser, VolunteerUser
from api.mixins import EagerLoadingMixin, DynamicFieldsMixin
from api.fields import LatLngField


class VolunteerOpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerOpportunity
        fields = '__all__'


class VolunteerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerUser
        fields = '__all__'


class VolunteerUserApplicationCreateSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, allow_blank=False, trim_whitespace=True)
    first_name = serializers.CharField(max_length=100, allow_blank=False, trim_whitespace=True)
    surnames = serializers.CharField(max_length=100, allow_blank=False, trim_whitespace=True)
    email = serializers.EmailField(allow_blank=False)
    age = serializers.IntegerField()

    opportunity_id = serializers.IntegerField(required=False)
    reason_why = serializers.CharField(max_length=280, allow_blank=False, trim_whitespace=True)


class VolunteerApplicationSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['user']

    user = VolunteerUserSerializer(read_only=True)

    class Meta:
        model = VolunteerApplication
        fields = '__all__'


class DonorHasUserSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [lambda: Prefetch('donoruser_set', queryset=DonorUser.objects.filter(is_active=True))]

    has_user = serializers.SerializerMethodField()

    class Meta:
        model = Donor
        fields = '__all__'

    def get_has_user(self, obj):
        return len(obj.donoruser_set.all()) > 0


class DonorMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = '__all__'


class DonationSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['donor']

    donor = DonorMiniSerializer(read_only=True)

    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ('action',)


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


class LocalitySerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    location = LatLngField()

    class Meta:
        model = Locality
        fields = (
            'id', 'cvegeo', 'cvegeo_municipality', 'cvegeo_state', 'location',
            'name', 'municipality_name', 'state_name', 'meta', 'has_data'
        )


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
    class Meta:
        model = Action
        fields = '__all__'


class SubmissionMediumSerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    images = serializers.SerializerMethodField()
    location = LatLngField()
    description = serializers.ReadOnlyField()
    address = serializers.ReadOnlyField()

    class Meta:
        model = Submission
        exclude = ('data',)

    def get_images(self, obj):
        return obj.synced_images(exclude_hidden=True)


class SubmissionSerializer(SubmissionMediumSerializer):
    _SELECT_RELATED_FIELDS = ['action']

    action = ActionSerializer(read_only=True)


class SubmissionMiniSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    location = LatLngField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = ('id', 'images', 'location')

    def get_images(self, obj):
        return obj.synced_images(exclude_hidden=True)


class ActionLocalitySerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['locality']

    locality = LocalitySerializer(read_only=True)

    class Meta:
        model = Action
        fields = ('id', 'locality', 'action_type', 'budget', 'organization_id')


class OrganizationMiniSerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    class Meta:
        model = Organization
        exclude = ('secret_key',)


class ActionMiniSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['locality', 'organization']

    locality = LocalitySerializer(read_only=True, _include_fields=('id', 'name', 'municipality_name', 'state_name'))
    organization = OrganizationMiniSerializer(read_only=True, _include_fields=('id', 'name'))

    class Meta:
        model = Action
        fields = ('id', 'key', 'organization', 'locality', 'action_type')


class ActionLocalityOrganizationSerializer(ActionLocalitySerializer):
    _SELECT_RELATED_FIELDS = ['locality', 'organization']

    locality = LocalitySerializer(read_only=True)
    organization = OrganizationMiniSerializer(read_only=True, _include_fields=('id', 'name'))

    class Meta:
        model = Action
        fields = ('id', 'locality', 'action_type', 'budget', 'organization')


class OrganizationSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [
        lambda: Prefetch('action_set', queryset=Action.objects.select_related('locality').filter(published=True))
    ]

    url = serializers.HyperlinkedIdentityField(view_name='api:organization-detail')
    actions = ActionLocalitySerializer(source='action_set', many=True, read_only=True)
    action_count = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        exclude = ('secret_key',)

    def get_action_count(self, obj):
        return obj.action_set.all().count()

    def get_image_count(self, obj):
        return sum(action.image_count for action in obj.action_set.all())

    def get_score(self, obj):
        return obj.score()


class EstablishmentSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    location = LatLngField()

    class Meta:
        model = Establishment
        fields = '__all__'


class ActionDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [
        lambda: Prefetch('submission_set', queryset=Submission.objects.filter(published=True)),
        lambda: Prefetch('donation_set', queryset=Donation.objects.select_related('donor').filter(
            approved_by_donor=True, approved_by_org=True)),
        lambda: Prefetch('volunteeropportunity_set', queryset=VolunteerOpportunity.objects.filter(published=True)),
    ]
    _SELECT_RELATED_FIELDS = ['locality', 'organization']

    locality = LocalitySerializer(read_only=True)
    organization = OrganizationMiniSerializer(read_only=True)
    submissions = SubmissionMediumSerializer(source='submission_set', many=True, read_only=True)
    donations = DonationSerializer(source='donation_set', many=True, read_only=True)
    opportunities = VolunteerOpportunitySerializer(source='volunteeropportunity_set', many=True, read_only=True)
    score = serializers.ReadOnlyField()

    class Meta:
        model = Action
        fields = '__all__'


class ActionSubmissionsSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [
        lambda: Prefetch('submission_set', queryset=Submission.objects.filter(published=True)),
        lambda: Prefetch('donation_set', queryset=Donation.objects.select_related('donor').filter(
            approved_by_donor=True, approved_by_org=True)),
    ]
    _SELECT_RELATED_FIELDS = ['locality', 'organization']

    locality = LocalitySerializer(read_only=True)
    organization = OrganizationMiniSerializer(read_only=True)
    submissions = SubmissionMiniSerializer(source='submission_set', many=True, read_only=True)
    donations = DonationSerializer(source='donation_set', many=True, read_only=True)
    score = serializers.ReadOnlyField()

    class Meta:
        model = Action
        fields = '__all__'


class OrganizationDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [
        lambda: Prefetch('action_set', queryset=Action.objects.select_related(
            'locality', 'organization'
        ).prefetch_related(
            Prefetch('submission_set', queryset=Submission.objects.filter(published=True)),
            Prefetch('donation_set', queryset=Donation.objects.select_related('donor').filter(
                approved_by_donor=True, approved_by_org=True)),
        ).filter(published=True))
    ]

    actions = ActionSubmissionsSerializer(source='action_set', many=True, read_only=True)
    action_count = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        exclude = ('secret_key',)

    def get_action_count(self, obj):
        return obj.action_set.all().count()

    def get_image_count(self, obj):
        return sum(action.image_count for action in obj.action_set.all())

    def get_score(self, obj):
        return obj.score()


class ActionLogSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    class Meta:
        model = ActionLog
        fields = '__all__'


class DonationDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['action__locality', 'action__organization']

    action = ActionMiniSerializer(read_only=True)

    class Meta:
        model = Donation
        fields = '__all__'


class DonationActionSubmissionsSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [
        lambda: Prefetch('action__submission_set', queryset=Submission.objects.filter(published=True)),
        lambda: Prefetch('action__donation_set', queryset=Donation.objects.select_related('donor').filter(
            approved_by_donor=True, approved_by_org=True)),
    ]
    _SELECT_RELATED_FIELDS = ['action__locality', 'action__organization']

    action = ActionSubmissionsSerializer(read_only=True)

    class Meta:
        model = Donation
        fields = '__all__'


class DonorSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [
        lambda: Prefetch('donation_set', queryset=Donation.objects.select_related(
            'action__locality', 'action__organization'
        ).filter(approved_by_donor=True, approved_by_org=True, action__published=True)),
        lambda: Prefetch('donoruser_set', queryset=DonorUser.objects.filter(is_active=True))
    ]

    donations = DonationDetailSerializer(source='donation_set', many=True, read_only=True)
    has_user = serializers.SerializerMethodField()
    metrics = serializers.SerializerMethodField()

    class Meta:
        model = Donor
        fields = '__all__'

    def get_has_user(self, obj):
        return len(obj.donoruser_set.all()) > 0

    def get_metrics(self, obj):
        actions, orgs = set(), set()
        total_donated = 0
        for donation in obj.donation_set.all():
            total_donated += donation.amount or 0
            actions.add(donation.action.id)
            orgs.add(donation.action.organization_id)
        return {'action_count': len(actions), 'org_count': len(orgs), 'total_donated': total_donated}


class VolunteerOpportunityDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['action__locality', 'action__organization']

    action = ActionLocalityOrganizationSerializer(read_only=True)

    class Meta:
        model = VolunteerOpportunity
        fields = '__all__'
