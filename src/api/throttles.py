"""Check `rest_framework.py` to see how throttling is set up in `REST_FRAMEWORK`
config dict.
"""
from rest_framework.throttling import UserRateThrottle


class NonAdminUserRateThrottle(UserRateThrottle):
    """Allow arbitrary number of admin requests, but limit requests from other
    authenticated users.
    """
    def allow_request(self, request, view):
        # `allow_request` must be called first, to ensure `self.history` is defined
        allow = super(NonAdminUserRateThrottle, self).allow_request(request, view)
        try:
            if request.user.is_staff:
                return True
        except AttributeError:
            pass
        return allow


class BurstRateThrottle(NonAdminUserRateThrottle):
    scope = 'burst'


class SustainedRateThrottle(NonAdminUserRateThrottle):
    scope = 'sustained'
