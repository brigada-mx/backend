import os
import hmac
import hashlib
from base64 import b64decode, b64encode
from urllib.parse import unquote, quote

from rest_framework.views import APIView
from rest_framework.response import Response

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


class DiscourseLogin(APIView):
    """View for obtaining an auth token by posting a valid email/password tuple.
    """
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = DiscourseLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sso = serializer.validated_data['sso']
        sig = serializer.validated_data['sig']
        user_type = serializer.validated_data['user_type']

        assert user_type in ('org', 'donor')
        serializer_class = {'org': OrganizationUserTokenSerializer, 'donor': DonorUserTokenSerializer}[user_type]
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        sso_secret = os.getenv('CUSTOM_DISCOURSE_SSO_SECRET')
        payload = unquote(sso)
        key = str.encode(sso_secret)
        signature = hmac.new(key, str.encode(payload), digestmod=hashlib.sha256).hexdigest()

        if signature != sig:
            return Response({'error': 'invalid_signature'}, status=400)

        if user_type == 'org':
            groups = ['reconstructores']
            try:
                if user.organization.donor:
                    groups.append('donadores')
            except:
                pass
            states = set()
            for action in user.organization.action_set.select_related('locality').all():
                if action.published:
                    states.add(discourse_transform(state_name_transform(action.locality.state_name)))
            groups += list(states)
            org_name = user.organization.name
            org_label = 'reconstructor'
            org_id = user.organization.id

        if user_type == 'donor':
            groups = ['donadores']
            if user.donor.organization:
                groups.append('reconstructores')
            org_name = user.donor.name
            org_label = 'donador'
            org_id = user.donor.id

        nonce_payload = b64decode(payload).decode()  # nonce=<nonce>
        org_link = f'https://app.brigada.mx/{org_label}es/{org_id}'
        payload_dict = {
          'name': f'{user.full_name} - {org_name}',
          'external_id': f'{user_type}-{user.pk}',
          'email': user.email,
          'username': discourse_transform(user.full_name),
          'bio': f'Estoy con el {org_label} [{org_name}]({org_link}).',  # make sure discourse default trust level >= 1
          'add_groups': ','.join(groups),
        }

        payload_parts = [nonce_payload] + [f'{k}={quote(v)}' for k, v in payload_dict.items()]
        payload = b64encode(str.encode('&'.join(payload_parts)))
        return Response(
            {'sso': quote(payload), 'sig': hmac.new(key, payload, digestmod=hashlib.sha256).hexdigest()}
        )
