from rest_framework import serializers

from db.map.models import Donor, Donation
from db.users.models import DonorUser
from api.mixins import EagerLoadingMixin
from api.serializers.serializers import authenticate
from api.serializers.map import DonorMiniSerializer


class DonorUserTokenSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email').strip()
        password = attrs.get('password').strip()

        user = authenticate(DonorUser, email, password)
        if not user:
            raise serializers.ValidationError('Unable to log in with provided credentials')

        attrs['user'] = user
        return attrs


class DonorUserSerializer(serializers.ModelSerializer):
    _SELECT_RELATED_FIELDS = ['donor']

    donor = DonorMiniSerializer(read_only=True)

    class Meta:
        model = DonorUser
        fields = ('email', 'full_name', 'first_name', 'surnames', 'is_active', 'donor')
        read_only_fields = ('email', 'is_active', 'full_name',)


class DonorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = ('name', 'desc', 'website')


class DonorReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = '__all__'


class DonorDonationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        exclude = ('donor', 'approved_by_org')


class DonorDonationUpdateSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ('donor', 'approved_by_org')
