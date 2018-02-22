from rest_framework import serializers

from db.map.models import Organization, Action, Submission
from db.users.models import OrganizationUser
from api.mixins import EagerLoadingMixin
from api.serializers.map import LocalityMediumSerializer, SubmissionMiniSerializer
from api.serializers.map import OrganizationMiniSerializer, SubmissionMediumSerializer


def authenticate(model, email, password):
    if not email or not password:
        return None
    user = model.objects.filter(email=email).first()
    if not user or not user.check_password(password):
        return None
    return user


class OrganizationUserTokenSerializer(serializers.Serializer):
    email = serializers.CharField()
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


class OrganizationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationUser
        fields = ('email', 'full_name', 'is_active',)
        read_only_fields = ('email', 'is_active',)


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('sector', 'name', 'desc', 'year_established', 'contact',)


class OrganizationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'


class AccountActionListCreateSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['locality']
    _PREFETCH_RELATED_FIELDS = ['submission_set']

    action_locality = LocalityMediumSerializer(source='locality', required=False, read_only=True)
    submissions = SubmissionMiniSerializer(source='submission_set', many=True, read_only=True)

    class Meta:
        model = Action
        fields = '__all__'
        read_only_fields = ('key', 'organization')


class AccountActionDetailSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['organization']
    _PREFETCH_RELATED_FIELDS = ['submission_set']

    organization = OrganizationMiniSerializer(read_only=True)
    submissions = SubmissionMediumSerializer(source='submission_set', many=True, read_only=True)

    class Meta:
        model = Action
        fields = '__all__'
        read_only_fields = ('key',)


class SubmissionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ('action', 'desc', 'addr', 'published')
