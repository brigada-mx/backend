from rest_framework.throttling import UserRateThrottle, ScopedRateThrottle


class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'


class SearchBurstRateScopedThrottle(ScopedRateThrottle):
    scope_attr = 'search_burst_throttle_scope'
