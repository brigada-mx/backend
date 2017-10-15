import django_filters
from rest_framework import filters

from database.nurses.models import NurseUser, Review
from api.filters import ListFilter, HasStringFilter, HasListFilter, RelatedObjectsCountFilter, DateRangeFilter, BooleanFilter, NotNullFilter


class NurseFilter(filters.FilterSet):
    """Filter `NurseUser`s by all kinds of attributes.
    """
    min_date = django_filters.DateFilter(name='join_date', lookup_expr='gte')
    max_date = django_filters.DateFilter(name='join_date', lookup_expr='lt')
    date_range_shift = DateRangeFilter(name='shifts__start')

    has_fcm_tokens = HasListFilter(name='fcm_tokens')
    has_messenger_id = HasStringFilter(name='messenger_id')
    reservation_id = django_filters.NumberFilter(name='shifts__reservation')

    gender = django_filters.CharFilter(name='gender')
    nurse_type = ListFilter(name='nurse_type')
    min_shifts = RelatedObjectsCountFilter(name='shifts', lookup_expr='gte', model=NurseUser)

    class Meta:
        model = NurseUser
        fields = ['nurse_type', 'gender',]


class NurseReviewFilter(filters.FilterSet):
    """Filter `NurseUser`s by all kinds of attributes.
    """
    shift_id = django_filters.NumberFilter(name='shift')
    nurse_id = django_filters.NumberFilter(name='shift__nurse_id')
    reservation_id = django_filters.NumberFilter(name='shift__reservation_id')
    is_public = BooleanFilter(name='is_public')

    has_rating = NotNullFilter(name='knowledge_rating')

    min_date = django_filters.DateFilter(name='date', lookup_expr='gte')
    max_date = django_filters.DateFilter(name='date', lookup_expr='lt')

    class Meta:
        model = Review
        fields = ['shift_id', 'nurse_id', 'reservation_id', 'is_public']
