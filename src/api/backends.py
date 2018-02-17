from django.contrib.auth.models import User
from django.conf import settings

from rest_framework import authentication
from rest_framework import exceptions

from db.users.models import OrganizationUserToken


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

        return (tkn.user, 'OrganizationUser')


class InternalAuthentication(authentication.BaseAuthentication):
    """Allows processes that run on our servers to authenticate with our API.
    """
    def authenticate(self, request):
        if not settings.SECRET_KEY == request.META.get('HTTP_AUTHORIZATION'):
            return None
        return (User(), 'InternalUser')
