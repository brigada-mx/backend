import django_filters
from rest_framework import filters

from database.reservations.models import Shift, ShiftIncident
from api.filters import NotNullFilter, NotZeroOrNullFilter, NumberMultipliedByFilter


class ShiftFilter(filters.FilterSet):
    """Filter shifts by all kinds of attributes, complements additional filters
    in the `ShiftList` view.
    """
    nurse_id = django_filters.NumberFilter(name='nurse_id')
    reservation_id = django_filters.NumberFilter(name='reservation_id')

    # `django_filters.DateFilter` automatically localizes target date/datetime instances before comparing them with filter params =)
    min_date = django_filters.DateFilter(name='start', lookup_expr='gte')
    max_date = django_filters.DateFilter(name='start', lookup_expr='lt')
    min_date_end = django_filters.DateFilter(name='end', lookup_expr='gte')
    max_date_end = django_filters.DateFilter(name='end', lookup_expr='lt')

    # DELETE THESE 2 FIELDS: nurse app legacy support, not needed for >=v2.8.0
    end_start_date = django_filters.DateFilter(name='end', lookup_expr='gte')
    end_end_date = django_filters.DateFilter(name='end', lookup_expr='lt')

    has_checkin = NotNullFilter(name='checkin')
    has_checkout = NotNullFilter(name='checkout')
    has_checkin_delay = NotZeroOrNullFilter(name='checkin_delay')
    max_checkin_delay = NumberMultipliedByFilter(name='checkin_delay', lookup_expr='lt', multiplied_by=60)

    class Meta:
        model = Shift
        fields = ['nurse_id', 'reservation_id', 'status',]


class ShiftIncidentFilter(filters.FilterSet):
    """Filter shift incidents by all kinds of attributes.

    Placing `shift` in the `fields` list causes infinite query loop =/.
    """
    reservation_id = django_filters.NumberFilter(name='shift__reservation_id')
    shift_id = django_filters.NumberFilter(name='shift_id')
    min_date = django_filters.DateFilter(name='shift__start', lookup_expr='gte')
    max_date = django_filters.DateFilter(name='shift__start', lookup_expr='lt')

    class Meta:
        model = ShiftIncident
        fields = ['shift_id', 'nurse_id', 'category',]
