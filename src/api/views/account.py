import os
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

from rest_framework import permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response

from db.map.models import Action, Submission, Donor, Donation, Organization
from db.users.models import OrganizationUser, OrganizationUserToken
from api.backends import OrganizationUserAuthentication
from api.serializers import AccountSubmissionSerializer, OrganizationUserSerializer, ArchiveSerializer
from api.serializers import PasswordSerializer, PasswordTokenSerializer, SendSetPasswordEmailSerializer
from api.serializers import OrganizationUserTokenSerializer, OrganizationReadSerializer
from api.serializers import DonorUserTokenSerializer, DiscourseLoginSerializer
from api.serializers import OrganizationUpdateSerializer, OrganizationCreateSerializer
from api.serializers import SubmissionUpdateSerializer, AccountActionDetailSerializer, AccountActionDetailReadSerializer
from api.serializers import AccountActionListSerializer, AccountActionCreateSerializer
from api.serializers import DonationSerializer, AccountDonationUpdateSerializer, AccountDonationCreateSerializer
from api.serializers import AccountSubmissionImageUpdateSerializer
from api.filters import ActionFilter, SubmissionFilter


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
        import hmac
        import hashlib
        from base64 import b64decode, b64encode
        from urllib.parse import unquote, quote

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

        if user_type == 'donor':
            groups = ['donadores']
            if user.donor.organization:
                groups.append('reconstructores')
            org_name = user.donor.name

        nonce_payload = b64decode(payload).decode()  # nonce=<nonce>
        payload_dict = {
          'name': f'{user.full_name} - {org_name}',
          'external_id': f'{user_type}-{user.pk}',
          'email': user.email,
          'username': discourse_transform(user.full_name),
          'bio': f'Estoy con el {"donador" if user_type == "donor" else "reconstructor"} {org_name}.',
          'add_groups': ','.join(groups),
        }

        payload_parts = [nonce_payload] + [f'{k}={quote(v)}' for k, v in payload_dict.items()]
        payload = b64encode(str.encode('&'.join(payload_parts)))
        return Response(
            {'sso': quote(payload), 'sig': hmac.new(key, payload, digestmod=hashlib.sha256).hexdigest()}
        )


class AccountSendSetPasswordEmail(APIView):
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = SendSetPasswordEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = OrganizationUser.objects.filter(email=email).first()
        if user is not None:
            if not user.is_active:
                return Response({'error': 'user not active'})
            user.send_set_password_email()
        return Response({'email': email})


class AccountSetPasswordWithToken(APIView):
    """Set org user's password, authenticating with token.
    """
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = PasswordTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(OrganizationUser, set_password_token=serializer.validated_data['token'])
        if not user.set_password_token_created or user.set_password_token_created < timezone.now() - timedelta(days=3):
            return Response({'error': 'This token has expired'}, status=403)
        user.set_password(serializer.validated_data['password'])
        user.set_password_token = ''
        user.save()
        return Response({'id': user.pk})


class AccountToken(APIView):
    """View for obtaining an auth token by posting a valid email/password tuple.
    """
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = OrganizationUserTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = OrganizationUserToken.objects.get_or_create(user=user)
        return Response({'token': token.key, 'id': user.pk, 'organization_id': user.organization.id})


class AccountDeleteToken(APIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        try:
            token = self.request.user.auth_token
        except ObjectDoesNotExist:
            return Response({}, status=400)
        else:
            token.delete()
            return Response({})


class AccountSetPassword(APIView):
    """Set org user's password. Requires passing old password for security.
    """
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({}, status=400)
        request.user.set_password(serializer.validated_data['password'])
        request.user.save()
        return Response({'id': request.user.pk})


class AccountMe(generics.RetrieveUpdateAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = OrganizationUserSerializer

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)


class AccountOrganizationResetKey(APIView):
    """View for obtaining an auth token by posting a valid email/password tuple.
    """
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        self.request.user.organization.reset_secret_key()
        return Response({'secret_key': self.request.user.organization.secret_key})


class AccountOrganizationRetrieveUpdate(generics.RetrieveUpdateAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return OrganizationUpdateSerializer
        return OrganizationReadSerializer

    def get_object(self):
        return self.request.user.organization

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)


class AccountOrganizationCreate(APIView):
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data['name']
        sector = serializer.validated_data['sector']
        email = serializer.validated_data['email']
        first_name = serializer.validated_data['first_name']
        surnames = serializer.validated_data['surnames']

        try:
            with transaction.atomic():
                organization = Organization.objects.create(name=name, sector=sector)
                OrganizationUser.objects.create(
                    organization=organization, email=email, first_name=first_name, surnames=surnames
                )
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        return Response({})


class AccountActionListCreate(generics.ListCreateAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    filter_class = ActionFilter

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return AccountActionCreateSerializer
        return AccountActionListSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Action.objects.filter(organization=self.request.user.organization)
        )

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class AccountActionRetrieveUpdate(generics.RetrieveUpdateAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return AccountActionDetailSerializer
        return AccountActionDetailReadSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Action.objects.filter(organization=self.request.user.organization)
        )

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)


class AccountActionRetrieveByKey(APIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer_class = AccountActionDetailReadSerializer
        action = get_object_or_404(
            serializer_class.setup_eager_loading(Action.objects.all()),
            organization=self.request.user.organization, key=kwargs['key']
        )
        return Response(serializer_class(action).data)


class AccountSubmissionList(generics.ListAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AccountSubmissionSerializer
    filter_class = SubmissionFilter

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Submission.objects.filter(organization=self.request.user.organization)
        )


class AccountSubmissionRetrieveUpdate(generics.RetrieveUpdateAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return SubmissionUpdateSerializer
        return AccountSubmissionSerializer

    def get_queryset(self):
        return Submission.objects.filter(organization=self.request.user.organization)

    def patch(self, request, *args, **kwargs):
        action = request.data.get('action', None)
        if action is not None:
            if action not in self.request.user.organization.action_set.values_list('pk', flat=True):
                return Response({'error': f'Action {action} does not belong to this organization'}, status=400)
        return super().patch(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)


class AccountSubmissionImageUpdate(APIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        submission = get_object_or_404(Submission, organization=self.request.user.organization, pk=kwargs['pk'])
        serializer = AccountSubmissionImageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        url = serializer.validated_data.pop('url', None)
        rotate = serializer.validated_data.pop('rotate', None)
        published = serializer.validated_data.pop('published', None)

        index, image = None, None
        for i, img in enumerate(submission.synced_images()):
            if img['url'] == url:
                index = i
                image = img
                break
        if image is None:
            return Response({'error': f'No image with this URL: {url}'}, status=404)

        if published is not None:
            image['hidden'] = not published
        if rotate is not None:
            if rotate == 'left':
                image['rotate'] = image.get('rotate', 0) - 1
            elif rotate == 'right':
                image['rotate'] = image.get('rotate', 0) + 1
            image['rotate'] = image['rotate'] % 4

        submission.image_urls[index] = image
        submission.save()
        return Response({'image': image})


class AccountDonationCreate(APIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = AccountDonationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        donor_name = serializer.validated_data.pop('donor_name', None)
        donor_id = serializer.validated_data.pop('donor_id', None)
        contact_email = serializer.validated_data.pop('contact_email', None)

        if donor_id is not None:  # `donor_id` takes precedence if both are passed
            donor = get_object_or_404(Donor, id=donor_id)
        else:
            donor = Donor.objects.filter(name=donor_name).first()
            if donor is None:
                donor = Donor.objects.create(name=donor_name)
        if contact_email:
            donor.add_contact_email(contact_email)

        action = serializer.validated_data.get('action')
        if action not in self.request.user.organization.action_set.all():
            return Response({'error': f'Action {action} does not belong to this organization'}, status=400)

        instance = Donation(donor=donor, **serializer.validated_data)
        instance.save(saved_by='org')
        return Response(serializer.data, status=201)


class AccountDonationRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return AccountDonationUpdateSerializer
        return DonationSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Donation.objects.filter(action__organization=self.request.user.organization)
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        for attr, value in serializer.validated_data.items():
            setattr(instance, attr, value)
        instance.save(saved_by='org')

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)


class AccountActionArchive(APIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        action = get_object_or_404(Action, organization=self.request.user.organization, pk=kwargs.get('pk', None))

        serializer = ArchiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        archived = serializer.validated_data['archived']

        if not archived:
            action.archived = False
        else:
            action.archived = True
            action.published = False
        action.save()
        return Response({'archived': archived})


class AccountSubmissionArchive(APIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        submission = get_object_or_404(
            Submission, organization=self.request.user.organization, pk=kwargs.get('pk', None))

        serializer = ArchiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        archived = serializer.validated_data['archived']

        if not archived:
            submission.archived = False
            submission.published = True
        else:
            submission.archived = True
            submission.published = False
            submission.action = None
        submission.save()
        return Response({'archived': archived})
