import os
import hmac
import hashlib
from base64 import b64decode, b64encode
from urllib.parse import unquote, quote

from rest_framework import serializers, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from db.users.models import OrganizationUser, DonorUser
from api.backends import OrganizationUserAuthentication, DonorUserAuthentication
from api.serializers import OrganizationUserTokenSerializer, DonorUserTokenSerializer, DiscourseLoginSerializer


def discourse_transform(s):
    table = str.maketrans({'á': 'a', 'é': 'e', 'í': 'i', 'ñ': 'n', 'ó': 'o', 'ú': 'u', 'ü': 'u'})
    username = s.lower().translate(table)
    return ''.join(ch for ch in username if ch.isalnum())


def state_name_transform(name):
    if name == 'Coahuila de Zaragoza':
        return 'Coahuila'
    if name == 'México':
        return 'Estado de México'
    if name == 'Veracruz de Ignacio de la Llave':
        return 'Veracruz'
    return name


def get_state_groups(user):
    states = set()
    for action in user.organization.action_set.select_related('locality').all():
        if action.published:
            states.add(discourse_transform(state_name_transform(action.locality.state_name)))
    return list(states)


def login(email, sso, sig):
    groups = []

    donor_user = DonorUser.objects.filter(email=email).first()
    if donor_user:
        user = donor_user
        user_type = 'donor'
        groups.append('donadores')
        org_name = donor_user.donor.name
        bio = f'Estoy con donador [{org_name}](https://app.brigada.mx/donadores/{donor_user.donor.id}).'

    org_user = OrganizationUser.objects.filter(email=email).first()  # org user takes precedence
    if org_user:
        user = org_user
        user_type = 'org'
        groups.append('reconstructores')
        groups += get_state_groups(org_user)
        org_name = org_user.organization.name
        bio = f'Estoy con [{org_name}](https://app.brigada.mx/reconstructores/{org_user.organization.id}).'

    sso_secret = os.getenv('CUSTOM_DISCOURSE_SSO_SECRET')
    payload = unquote(sso)
    key = str.encode(sso_secret)
    signature = hmac.new(key, str.encode(payload), digestmod=hashlib.sha256).hexdigest()

    if signature != sig:
        return Response({'error': 'invalid_signature'}, status=400)

    nonce_payload = b64decode(payload).decode()  # nonce=<nonce>
    payload_dict = {
      'name': f'{user.full_name} - {org_name}',
      'external_id': f'{user_type}-{user.pk}',
      'email': user.email,
      'username': discourse_transform(user.full_name),
      'bio': bio,  # make sure discourse default trust level >= 1, or links are disabled
      'add_groups': ','.join(groups),
    }

    payload_parts = [nonce_payload] + [f'{k}={quote(v)}' for k, v in payload_dict.items()]
    payload = b64encode(str.encode('&'.join(payload_parts)))
    return Response(
        {'sso': quote(payload), 'sig': hmac.new(key, payload, digestmod=hashlib.sha256).hexdigest()}
    )


class DiscourseLogin(APIView):
    """View for obtaining an auth token by posting a valid email/password tuple,
    for either org user or donor user.
    """
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = DiscourseLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sso = serializer.validated_data['sso']
        sig = serializer.validated_data['sig']

        serializer = DonorUserTokenSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            serializer = OrganizationUserTokenSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['user'].email
        return login(email, sso, sig)


class DiscourseAuthLogin(APIView):
    """View for obtaining an auth token by posting a valid email/password tuple,
    for either org user or donor user.
    """
    authentication_classes = (OrganizationUserAuthentication, DonorUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = DiscourseLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sso = serializer.validated_data['sso']
        sig = serializer.validated_data['sig']

        email = request.user.email
        return login(email, sso, sig)
