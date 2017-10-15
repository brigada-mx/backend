REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'api.exceptions.custom_exception_handler',
    # allow client to override using `?page_size={num}` in query string
    'DEFAULT_PAGINATION_CLASS': 'api.paginators.StandardResultsSetPagination',
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'api.throttles.BurstRateThrottle',
        'api.throttles.SustainedRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'burst': '30/min', # applies to all authenticated users, including w/ token auth, except admins
        'sustained': '2000/day', # applies to all authenticated users, including w/ token auth, except admins
        'anon': '20/day', # applies to all unauthenticated users

        # SCOPED THROTTLES
        'unauthenticated': '20/day', # special throttle for unauthenticated requests used, e.g., in account creation
        'authentication': '10/day', # for users submitting username/email/password tuples to obtain token
    },
}

# This setting is IMPORTANT: without it, rest_framework.reverse.reverse, which is
# also used in related fields, and which invokes request.build_absolute_uri, will
# never be able to set the correct protocol/scheme for the absolute URLs that it
# generates. If the django server receives requests via a load balancer, make sure
# the balancer forwards the protocol, e.g.
# proxy_set_header X-Forwarded-Proto $scheme;
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
