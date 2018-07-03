from rest_framework import serializers

from db.map.models import Donor, Donation
from db.users.models import DonorUser
from api.serializers.map import DonorMiniSerializer
from .base import authenticate, Serializer, ModelSerializer


class DonorUserTokenSerializer(Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email').strip()
        password = attrs.get('password').strip()

        user = authenticate(DonorUser, email, password)
        if not user:
            raise serializers.ValidationError('Unable to log in with provided credentials')

        attrs['user'] = user
        return attrs


class DonorUserSerializer(ModelSerializer):
    _SELECT_RELATED_FIELDS = ['donor']

    donor = DonorMiniSerializer(read_only=True)

    class Meta:
        model = DonorUser
        fields = ('email', 'full_name', 'first_name', 'surnames', 'is_active', 'donor')
        read_only_fields = ('email', 'is_active', 'full_name')


class DonorUpdateSerializer(ModelSerializer):
    class Meta:
        model = Donor
        fields = ('sector', 'name', 'desc', 'year_established', 'contact', 'donating', 'donating_desc')


class DonorReadSerializer(ModelSerializer):
    class Meta:
        model = Donor
        fields = '__all__'


class DonorDonationCreateSerializer(ModelSerializer):
    class Meta:
        model = Donation
        exclude = ('donor', 'approved_by_org')


class DonorDonationUpdateSerializer(ModelSerializer):
    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ('donor', 'approved_by_org')


class DonorCreateSerializer(Serializer):
    sector = serializers.CharField(allow_blank=False)
    donor_id = serializers.IntegerField(required=False)
    donor_name = serializers.CharField(required=False, trim_whitespace=True)

    email = serializers.EmailField(allow_blank=False)
    first_name = serializers.CharField(max_length=100, allow_blank=False, trim_whitespace=True)
    surnames = serializers.CharField(max_length=100, allow_blank=False, trim_whitespace=True)
