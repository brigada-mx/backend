from django.db.models import Prefetch
from rest_framework import serializers

from db.map.models import Organization, Action, Submission, Testimonial, Donation
from db.map.models import VolunteerOpportunity, VolunteerApplication
from db.users.models import VolunteerUser, OrganizationUser
from api.fields import LatLngField
from api.mixins import EagerLoadingMixin, DynamicFieldsMixin
from api.serializers.serializers import authenticate
from api.serializers.map import LocalitySerializer, DonationSerializer, ActionSerializer
from api.serializers.map import OrganizationMiniSerializer, SubmissionMediumSerializer, TestimonialMediumSerializer
from api.serializers.map import VolunteerApplicationSerializer, VolunteerOpportunitySerializer


class ArchiveSerializer(serializers.Serializer):
    archived = serializers.BooleanField()


class OrganizationUserTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email').strip()
        password = attrs.get('password').strip()

        user = authenticate(OrganizationUser, email, password)
        if not user:
            raise serializers.ValidationError('Unable to log in with provided credentials')

        attrs['user'] = user
        return attrs


class SendSetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(allow_blank=False, trim_whitespace=True)
    password = serializers.CharField(min_length=8, max_length=None, allow_blank=False, trim_whitespace=True)


class PasswordTokenSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8, max_length=None, allow_blank=False, trim_whitespace=True)
    token = serializers.CharField(min_length=20, max_length=None, allow_blank=False, trim_whitespace=True)
    created = serializers.BooleanField(required=False, default=False)


class OrganizationCreateSerializer(serializers.Serializer):
    sector = serializers.CharField(allow_blank=False)
    name = serializers.CharField(allow_blank=False, trim_whitespace=True)

    email = serializers.EmailField(allow_blank=False)
    first_name = serializers.CharField(max_length=100, allow_blank=False, trim_whitespace=True)
    surnames = serializers.CharField(max_length=100, allow_blank=False, trim_whitespace=True)


class OrganizationUserSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['organization']

    organization = OrganizationMiniSerializer(read_only=True)

    class Meta:
        model = OrganizationUser
        fields = ('email', 'full_name', 'first_name', 'surnames', 'is_active', 'organization')
        read_only_fields = ('email', 'is_active', 'full_name')


class VolunteerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerUser
        exclude = ('password',)


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('sector', 'name', 'desc', 'year_established', 'contact')


class OrganizationReadSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = '__all__'

    def get_score(self, obj):
        return obj.score()


class AccountActionListSerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['locality']

    locality = LocalitySerializer(read_only=True)

    class Meta:
        model = Action
        fields = '__all__'


class AccountActionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = '__all__'
        read_only_fields = ('key', 'organization', 'status_by_category', 'score', 'level')


class AccountActionDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [lambda: Prefetch('donation_set', queryset=Donation.objects.select_related('donor'))]
    _PREFETCH_RELATED_FIELDS = ['submission_set', 'volunteeropportunity_set', 'testimonial_set']
    _SELECT_RELATED_FIELDS = ['organization']

    organization = OrganizationMiniSerializer(read_only=True)
    submissions = SubmissionMediumSerializer(source='submission_set', many=True, read_only=True)
    testimonials = TestimonialMediumSerializer(source='testimonial_set', many=True, read_only=True)
    donations = DonationSerializer(source='donation_set', many=True, read_only=True)
    opportunities = VolunteerOpportunitySerializer(source='volunteeropportunity_set', many=True, read_only=True)

    class Meta:
        model = Action
        fields = '__all__'
        read_only_fields = ('key', 'deleted', 'status_by_category', 'score', 'level')


class AccountActionDetailReadSerializer(AccountActionDetailSerializer):
    _SELECT_RELATED_FIELDS = ['organization', 'locality']

    locality = LocalitySerializer(read_only=True)


class AccountSubmissionSerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['action']

    action = ActionSerializer(read_only=True)

    images = serializers.SerializerMethodField()
    location = LatLngField()
    description = serializers.ReadOnlyField()
    address = serializers.ReadOnlyField()

    class Meta:
        model = Submission
        exclude = ('data',)

    def get_images(self, obj):
        return obj.synced_images()


class AccountSubmissionCreateSerializer(serializers.ModelSerializer):
    location = LatLngField()

    class Meta:
        model = Submission
        fields = '__all__'
        read_only_fields = ('organization', 'source', 'source_id', 'data')


class AccountSubmissionUpdateSerializer(serializers.ModelSerializer):
    location = LatLngField()

    class Meta:
        model = Submission
        fields = ('action', 'desc', 'addr', 'published', 'submitted', 'location')


class AccountSubmissionImageUpdateSerializer(serializers.Serializer):
    url = serializers.URLField()
    published = serializers.BooleanField(required=False)
    rotate = serializers.RegexField(regex=r'^left|right$', required=False)


class AccountTestimonialSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['action']

    action = ActionSerializer(read_only=True)
    location = LatLngField()

    class Meta:
        model = Testimonial
        fields = '__all__'


class AccountTestimonialCreateSerializer(serializers.ModelSerializer):
    location = LatLngField()

    class Meta:
        model = Testimonial
        fields = '__all__'


class AccountTestimonialUpdateSerializer(serializers.ModelSerializer):
    location = LatLngField()

    class Meta:
        model = Testimonial
        exclude = ('video',)


class AccountDonationCreateSerializer(serializers.ModelSerializer):
    donor_id = serializers.IntegerField(required=False)
    donor_name = serializers.CharField(required=False)
    contact_email = serializers.EmailField(required=False)

    class Meta:
        model = Donation
        exclude = ('donor', 'approved_by_donor')


class AccountDonationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ('action', 'approved_by_donor')


class VolunteerOpportunityCreateSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    class Meta:
        model = VolunteerOpportunity
        fields = '__all__'


class AccountVolunteerOpportunityDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [
        lambda: Prefetch('volunteerapplication_set', queryset=VolunteerApplication.objects.select_related('user'))
    ]

    applications = VolunteerApplicationSerializer(source='volunteerapplication_set', many=True, read_only=True)

    class Meta:
        model = VolunteerOpportunity
        fields = '__all__'
