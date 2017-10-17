from django.contrib.auth.models import User
from django.conf import settings

from rest_framework import authentication


class InternalAuthentication(authentication.BaseAuthentication):
    """Allows processes that run on our servers to authenticate with our API by
    presenting our secret key.
    """
    def authenticate(self, request):
        if not settings.SECRET_KEY == request.META.get('HTTP_AUTHORIZATION'):
            return None
        return (User(), 'InternalUser')
