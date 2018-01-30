from rest_framework.throttling import UserRateThrottle, ScopedRateThrottle


class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'


class SustainedRateThrottle(UserRateThrottle):
    scope = 'sustained'


class SearchBurstRateScopedThrottle(ScopedRateThrottle):
    scope_attr = 'search_burst_throttle_scope'


class SearchSustainedRateScopedThrottle(ScopedRateThrottle):
    scope_attr = 'search_sustained_throttle_scope'
