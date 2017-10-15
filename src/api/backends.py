from time import time

from django.contrib.auth.models import User
from django.conf import settings
from django.core import signing

from rest_framework import authentication
from rest_framework import exceptions

from api.models import NurseUserToken, ClientUserToken
from database.nurses.models import NurseUser


class NurseTokenAuthentication(authentication.BaseAuthentication):
    """This auth class allows client to specify a user type to short circuit
    authentication without any DB lookups, skipping to the next auth class.

    This allows us to have views with multiple auth classes that suffer no
    performance issues.
    """
    def authenticate(self, request):
        # allow client to specify user type to avoid extra lookups in DB
        auth_type = request.META.get('HTTP_X_ASISTIA_AUTH_TYPE')
        # if client specified a different `auth_type` (not nurse), authentication fails immediately, next backend is tried
        if auth_type and auth_type != 'nurse_token':
            return None

        token = request.META.get('HTTP_AUTHORIZATION') # get auth token from header
        if not token:
            return None

        try:
            tkn = NurseUserToken.objects.get(key=token)
        except NurseUserToken.DoesNotExist:
            # if client didn't specify `auth_type`, don't raise exception, because other backends should be tried
            if not auth_type:
                return None
            # if client specified nurse `auth_type`, raise exception so that no other backends are tried
            raise exceptions.AuthenticationFailed('invalid_token')

        return (tkn.user, 'NurseUser')


class UnauthenticatedNurse(authentication.BaseAuthentication):
    """This auth class allows nurse to be authenticated after creating an account
    but without signing up yet.

    This allows us to "authenticate" a nurse with the token created
    after POSTing to `/nurses/create/` through our mobile app.
    For now we only use this to update a NurseUser, so if we are not hitting
    the desired endpoint with PUT or PATCH just skip this Backend.
    """
    def authenticate(self, request):
        method = request.method.lower()

        if method not in ['put', 'patch', 'post']:
            return None

        try:
            token = request.data.get('token')
            payload = signing.loads(token)
        except Exception as e:
            # token_deserialization_error
            return None

        nurse_id = payload.get('nurse_id')
        if payload.get('expires') < time() or payload.get('namespace') != 'update_nurse_unauthenticated':
            return None

        try:
            nurse = NurseUser.objects.get(id=nurse_id)
        except NurseUser.DoesNotExist:
            raise exceptions.AuthenticationFailed('invalid_token')
        return (nurse, 'NurseUser')


class ClientTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_type = request.META.get('HTTP_X_ASISTIA_AUTH_TYPE')
        if auth_type and auth_type != 'client_token':
            return None

        token = request.META.get('HTTP_AUTHORIZATION')
        if not token:
            return None

        try:
            tkn = ClientUserToken.objects.get(key=token)
        except ClientUserToken.DoesNotExist:
            if not auth_type:
                return None
            raise exceptions.AuthenticationFailed('invalid_token')

        return (tkn.user, 'ClientUser')


class InternalAuthentication(authentication.BaseAuthentication):
    """Allows processes that run on our servers to authenticate with our API by
    presenting our secret key.
    """
    def authenticate(self, request):
        if not settings.SECRET_KEY == request.META.get('HTTP_AUTHORIZATION'):
            return None
        return (User(), 'InternalUser')
