import django_filters
from rest_framework import filters

from database.clients.models import ClientUser, ActivityFeedItem
from api.filters import HasListFilter


class ActivityFeedItemFilter(filters.FilterSet):
    """Filter `NurseUser`s by all kinds of attributes.
    """
    min_date = django_filters.DateFilter(name='date', lookup_expr='gte')
    max_date = django_filters.DateFilter(name='date', lookup_expr='lt')

    class Meta:
        model = ActivityFeedItem
        fields = '__all__'


class ClientFilter(filters.FilterSet):
    """Filter `NurseUser`s by all kinds of attributes.
    """
    min_date = django_filters.DateFilter(name='join_date', lookup_expr='gte')
    max_date = django_filters.DateFilter(name='join_date', lookup_expr='lt')

    has_fcm_tokens = HasListFilter(name='fcm_tokens')
    status = django_filters.NumberFilter(name='reservation__status')

    class Meta:
        model = ClientUser
        fields = ('reservation', 'account_holder',)
