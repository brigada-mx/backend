import django_filters
from rest_framework import filters

from database.patients.models import CareLogEntry
from api.filters import ListFilter, NotNullFilter, BooleanFilter


class CareLogEntryFilter(filters.FilterSet):
    nurse_id = django_filters.NumberFilter(name="shift__nurse_id")
    reservation_id = django_filters.NumberFilter(name="shift__reservation_id")
    shift_id = django_filters.NumberFilter(name="shift_id")
    patient_id = django_filters.NumberFilter(name="patient_id")

    min_date = django_filters.DateFilter(name='start', lookup_expr='gte')
    max_date = django_filters.DateFilter(name='start', lookup_expr='lt')
    min_date_shift = django_filters.DateFilter(name='shift__start', lookup_expr='gte')
    max_date_shift = django_filters.DateFilter(name='shift__start', lookup_expr='lt')
    min_date_end_shift = django_filters.DateFilter(name='shift__end', lookup_expr='gte')
    max_date_end_shift = django_filters.DateFilter(name='shift__end', lookup_expr='lt')

    status = ListFilter(name='status')
    has_observations = NotNullFilter(name='observations')
    created_by_nurse = BooleanFilter(name='created_by_nurse')
    tasks = ListFilter(name='task__task')

    class Meta:
        model = CareLogEntry
        fields = ['nurse_id', 'reservation_id', 'shift_id', 'patient_id', 'task', 'status',]
