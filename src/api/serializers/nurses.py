from django.utils import timezone
from django.db.models import Prefetch
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from rest_framework import serializers
from rest_framework.reverse import reverse

from database.reservations.models import Shift
from database.nurses.models import NurseUser, Review
from api.fields import LatLngField
from api.mixins import EagerLoadingMixin, DynamicFieldsMixin


class NurseSendPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    email_type = serializers.ChoiceField(choices=('create', 'reset', 'create_admin',))


class NurseUserAuthTokenSerializer(serializers.Serializer):
    """Parses a phone and an email and returns a token for authenticating
    requests of `NurseUser` instances.
    """
    email = serializers.CharField(label=_("email"))
    password = serializers.CharField(label=_("password"), style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = self.authenticate(email=email, password=password)

            if user is None:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg)

        attrs['user'] = user
        return attrs

    def authenticate(self, email, password):
        try:
            nurse = NurseUser.objects.get(email=email.strip()) # help nurses out by removing whitespace from email
        except NurseUser.DoesNotExist:
            return None

        if nurse.check_password(password):
            return nurse
        return None

    @staticmethod
    def clean_phone(phone):
        """Remove all non-numeric chars from input and stored value. Eliminates
        login confusion involving parentheses, dashes, spaces, etc without
        compromising security.
        """
        return ''.join(ch for ch in phone if ch.isdigit())


class NurseUserCreateSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    url = serializers.HyperlinkedIdentityField(view_name='api:nurse-detail')
    full_name = serializers.SerializerMethodField()
    password = serializers.CharField(label=_("password"), style={'input_type': 'password'})

    class Meta:
        model = NurseUser
        fields = ['first_name', 'surname', 'email', 'password', 'gender', 'nurse_type', 'phone', 'url', 'full_name']

    def get_full_name(self, obj):
        return obj.full_name


class NurseUserSerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    _PREFETCH_FUNCTIONS = [lambda: Prefetch('shifts', queryset=Shift.objects.all().select_related('review', 'reservation'), to_attr='_shifts')]

    url = serializers.HyperlinkedIdentityField(view_name='api:nurse-detail')
    url_admin = serializers.SerializerMethodField()
    add_fcm_token_url = serializers.SerializerMethodField()
    public_profile_url = serializers.SerializerMethodField()

    nurse_type_gendered = serializers.SerializerMethodField()
    location = LatLngField()
    full_name = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = NurseUser
        fields = '__all__'
        read_only_fields = ('id', 'is_active', 'join_date', 'nurse_type', 'slug', 'years_experience', 'messenger_id', 'public_profile_url', 'full_name', 'photo_thumbnail',)
        # if `fields` is defined for a serializer, then fields present in `read_only_fields` will only be included
        # if they are also included in `fields`: https://github.com/tomchristie/django-rest-framework/issues/2391

    def get_url_admin(self, obj):
        return reverse('staff:nurses:update', args=[obj.pk], request=self.context.get('request'))

    def get_add_fcm_token_url(self, obj):
        return reverse('api:nurse-add-fcm-token', request=self.context.get('request'))

    def get_nurse_type_gendered(self, obj):
        return obj.nurse_type_gendered

    def get_public_profile_url(self, obj):
        return obj.public_profile_url

    def get_full_name(self, obj):
        return obj.full_name

    def get_rating(self, obj):
        return obj.rating


class NurseUserDetailSerializer(NurseUserSerializer):
    _PREFETCH_FUNCTIONS = NurseUserSerializer._PREFETCH_FUNCTIONS + [lambda: Prefetch('shifts', queryset=Shift.objects.order_by('start').filter(start__lt=timezone.now()), to_attr='past_shifts')]

    metrics = serializers.SerializerMethodField()

    def get_metrics(self, obj):
        shifts_covered, approximate_hours_covered, on_time_shifts, first_shift_date = 0, 0, 0, 0, None
        shifts = obj.past_shifts
        for shift in shifts:
            shifts_covered += 1
            approximate_hours_covered += shift.total_hours
            if shift.checkin and (shift.checkin-shift.start).total_seconds() // 900 <= 0:
                on_time_shifts += 1
        if len(shifts):
            first_shift_date = shifts[0].start.date()

        return {
            'shifts_covered': shifts_covered,
            'approximate_hours_covered': approximate_hours_covered,
            'on_time_shift_rate': on_time_shifts / max(1, len(shifts)),
            'first_shift_date': first_shift_date,
        }


class NurseUserNoRequestSerializer(serializers.ModelSerializer):
    """Serializer that won't choke if `request` isn't passed in context.
    """
    url_admin = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = NurseUser
        fields = ('email', 'fcm_tokens', 'full_name', 'gender', 'id', 'nurse_type', 'url_admin', 'messenger_id', 'phone',)

    def get_url_admin(self, obj):
        return '{}{}'.format( settings.SITE_URL, reverse('staff:nurses:update', args=[obj.pk]) )

    def get_full_name(self, obj):
        return obj.full_name


class NurseUserSubsetSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = NurseUser
        fields = ('photo', 'photo_thumbnail', 'email', 'phone', 'full_name')

    def get_full_name(self, obj):
        return obj.full_name


class NurseReviewSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['shift__reservation', 'shift__nurse']

    url = serializers.HyperlinkedIdentityField(view_name='api:nursereview-detail')
    shift = serializers.HyperlinkedRelatedField(view_name='api:shift-detail', read_only=True)
    rating = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    nurse = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('shift', 'date', 'is_public', 'token')

    def get_rating(self, obj):
        return obj.rating

    def get_is_expired(self, obj):
        return obj.is_expired

    def get_is_completed(self, obj):
        return obj.is_completed

    def get_nurse(self, obj):
        nurse = NurseUserSubsetSerializer(obj.shift.nurse)
        return nurse.data
