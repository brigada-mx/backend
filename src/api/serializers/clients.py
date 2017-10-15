import copy

from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.reverse import reverse

from database.clients.models import ClientUser, Card, ActivityFeedItem
from database.payments.models.providers import PROVIDER_CHOICES
from api.mixins import EagerLoadingMixin, DynamicFieldsMixin
from api.helpers import error_response_json
from api.serializers import ReservationSerializer, ReservationDetailSerializer


class ClientUserSerializer(DynamicFieldsMixin, serializers.ModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['reservation',]

    full_name = serializers.SerializerMethodField()
    add_fcm_token_url = serializers.SerializerMethodField()

    change_account_holder_url = serializers.HyperlinkedIdentityField(view_name='api:client-change-account-holder')
    url = serializers.HyperlinkedIdentityField(view_name='api:client-detail')
    reservation = ReservationSerializer(read_only=True, required=False)

    class Meta:
        model = ClientUser
        exclude = ('openpay_id', 'conekta_id', 'id_img_back', 'id_img_front', 'set_password_code', 'password',)

    def get_full_name(self, obj):
        return obj.full_name

    def get_add_fcm_token_url(self, obj):
        return reverse('api:client-add-fcm-token', request=self.context.get('request'))


class ClientUserDetailSerializer(ClientUserSerializer):
    reservation = ReservationDetailSerializer(read_only=True)


class ClientUserAuthTokenSerializer(serializers.Serializer):
    """Parses an email and password and returns a token for authenticating
    requests of `ClientUser` instances.

    Lifted from:
    https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/authtoken/serializers.py
    """
    email = serializers.CharField(label=_("email"))
    password = serializers.CharField(label=_("password"), style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # https://docs.djangoproject.com/en/1.10/ref/contrib/auth/#django.contrib.auth.backends.ModelBackend.authenticate
            # this works because `USERNAME_FIELD` for all our user models is `email` instead of `username`
            user = authenticate(username=email, password=password, auth_client=True)
            # this will invoke `authenticate` for backends in `settings.AUTHENTICATION_BACKENDS`
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg)
            else:
                if user.reservation.status == 3:
                    raise PermissionDenied(
                        error_response_json("User's account was terminated.", 'Tu cuenta fue terminada.',
                                            error_type='account_terminated'))
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg)

        attrs['user'] = user
        return attrs


class ClientSendPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    email_type = serializers.ChoiceField(choices=('create', 'create_admin', 'reset', 'invite_carecircle', 'invite_client',))


class ClientCreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    surname = serializers.CharField()
    phone = serializers.CharField()


class CardTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    provider = serializers.ChoiceField(choices=PROVIDER_CHOICES)
    antifraud_token = serializers.CharField(required=False)
    is_valid = serializers.BooleanField(read_only=True)
    error = serializers.CharField(read_only=True)


class ClientCardsSerializer(serializers.Serializer):
    cards = CardTokenSerializer(many=True, allow_empty=False)

    def create(self, validated_data):
        client = validated_data.get('client')
        cards = validated_data.get('cards')
        validated_cards = []
        for card in cards:
            validated_card = copy.deepcopy(card)
            antifraud_token = card.get('antifraud_token')
            card_obj = Card(client=client, token=card.get('token'), provider=card.get('provider'))
            # Be aware that this method saves the instance if it's correctly added to the client.
            is_valid, error_text = card_obj.validate_token(antifraud_token=antifraud_token)
            validated_card['is_valid'] = is_valid
            validated_card['error'] = error_text
            validated_cards.append(validated_card)
        return {'cards': validated_cards}


class ActivityFeedItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = ActivityFeedItem
        fields = '__all__'
