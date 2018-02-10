REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'api.exceptions.custom_exception_handler',
    # allow client to override using `?page_size={num}` in query string
    'DEFAULT_PAGINATION_CLASS': 'api.paginators.NoCountPagination',
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'api.throttles.BurstRateThrottle',
        'api.throttles.SearchBurstRateScopedThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        # applies to all authenticated users, including w/ token auth, except admins
        'burst': '30/min',
        'search_burst': '80/min',
    },
}

# This setting is IMPORTANT: without it, rest_framework.reverse.reverse, which is
# also used in related fields, and which invokes request.build_absolute_uri, will
# never be able to set the correct protocol/scheme for the absolute URLs that it
# generates. If the django server receives requests via a load balancer, make sure
# the balancer forwards the protocol, e.g.
# proxy_set_header X-Forwarded-Proto $scheme;
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
