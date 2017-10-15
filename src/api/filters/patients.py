import django_filters
from rest_framework import filters

from database.patients.models import Patient


class PatientFilter(filters.FilterSet):
    min_date = django_filters.DateFilter(name='created', lookup_expr='gte')
    max_date = django_filters.DateFilter(name='created', lookup_expr='lt')
    reservation_id = django_filters.NumberFilter(name="reservation_id")

    class Meta:
        model = Patient
        fields = ['reservation_id',]
