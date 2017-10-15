import django_filters
from rest_framework import filters

from database.reservations.models import ShiftSchedulePostingResponse
from api.filters import ListFilter, NotNullFilter, NumberMultipliedByFilter


class PostingResponseFilter(filters.FilterSet):
    """Filter `ShiftSchedulePostingResponse`s by all kinds of attributes.
    """
    nurse_id = django_filters.NumberFilter(name="shift__nurse_id")

    min_date = django_filters.DateFilter(name='created', lookup_expr='gte')
    max_date = django_filters.DateFilter(name='created', lookup_expr='lt')

    has_responded = NotNullFilter(name='responded')
    can_cover = ListFilter(name='can_cover')
    max_response_delay = NumberMultipliedByFilter(name='response_delay', lookup_expr='lt', multiplied_by=60)

    class Meta:
        model = ShiftSchedulePostingResponse
        fields = ['nurse_id',]
