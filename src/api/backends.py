from django.contrib.auth.models import User
from django.conf import settings

from rest_framework import authentication
from rest_framework import exceptions

from db.users.models import OrganizationUserToken, DonorUserToken


class OrganizationUserAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION')
        if not auth:
            return None
        try:
            _, token = auth.split()
        except:
            return None

        try:
            tkn = OrganizationUserToken.objects.get(key=token)
        except OrganizationUserToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('invalid_token')
        if not tkn.user.is_active:
            raise exceptions.AuthenticationFailed('invalid_token')

        return (tkn.user, 'OrganizationUser')


class DonorUserAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION')
        if not auth:
            return None
        try:
            _, token = auth.split()
        except:
            return None

        try:
            tkn = DonorUserToken.objects.get(key=token)
        except DonorUserToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('invalid_token')
        if not tkn.user.is_active:
            raise exceptions.AuthenticationFailed('invalid_token')

        return (tkn.user, 'DonorUser')


class InternalAuthentication(authentication.BaseAuthentication):
    """Allows processes that run on our servers to authenticate with our API.
    """
    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        try:
            _, token = auth.split()
        except:
            return None

        if not settings.SECRET_KEY == token:
            return None
        return (User(), 'InternalUser')
