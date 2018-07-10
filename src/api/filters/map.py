from typing import Callable

import django_filters
from django_filters import rest_framework as filters

from db.map.models import Action, Establishment, Submission, Donation, Testimonial, VolunteerOpportunity
from .base import parse_boolean, BooleanFilter


def scian_category_filter(queryset, name, value):
    boolean = parse_boolean(value)
    if boolean is None:
        return queryset
    if boolean is False:
        return queryset.filter(scian_group_id=1)
    return queryset.exclude(scian_group_id=1)


def has_field_filter_factory(field: str) -> Callable:
    def has_field_filter(queryset, name, value):
        boolean = parse_boolean(value)
        if boolean is None:
            return queryset
        if boolean is False:
            return queryset.filter(**{f'{field}__isnull': True})
        return queryset.filter(**{f'{field}__isnull': False})
    return has_field_filter


class ActionFilter(filters.FilterSet):
    locality_id = django_filters.NumberFilter(name='locality')
    organization_id = django_filters.NumberFilter(name='organization')
    archived = BooleanFilter(name='archived')
    level__gte = django_filters.NumberFilter(name='level', lookup_expr='gte')
    level__lte = django_filters.NumberFilter(name='level', lookup_expr='lte')
    has_start_date = django_filters.Filter(method=has_field_filter_factory('start_date'))

    class Meta:
        model = Action
        fields = ['locality_id', 'organization_id', 'archived']


class VolunteerOpportunityFilter(filters.FilterSet):
    action_id = django_filters.NumberFilter(name='action')
    published = BooleanFilter(name='published')
    transparency_level = django_filters.NumberFilter(name='action__level')
    transparency_level__gte = django_filters.NumberFilter(name='action__level', lookup_expr='gte')
    transparency_level__lte = django_filters.NumberFilter(name='action__level', lookup_expr='lte')

    class Meta:
        model = VolunteerOpportunity
        fields = ['action_id', 'published', 'transparency_level']


class EstablishmentFilter(filters.FilterSet):
    locality_id = django_filters.NumberFilter(name='locality')
    is_categorized = django_filters.Filter(method=scian_category_filter)

    class Meta:
        model = Establishment
        fields = ['locality_id']


class SubmissionFilter(filters.FilterSet):
    action_id = django_filters.NumberFilter(name='action')
    organization_id = BooleanFilter(name='organization')
    published = BooleanFilter(name='published')
    archived = BooleanFilter(name='archived')
    has_action = django_filters.Filter(method=has_field_filter_factory('action'))

    class Meta:
        model = Submission
        fields = ['action_id', 'organization_id', 'published', 'archived']


class TestimonialFilter(filters.FilterSet):
    action_id = django_filters.NumberFilter(name='action')
    published = BooleanFilter(name='published')
    archived = BooleanFilter(name='archived')

    class Meta:
        model = Testimonial
        fields = ['action_id', 'published', 'archived']


class DonationFilter(filters.FilterSet):
    donor_id = django_filters.NumberFilter(name='donor')

    class Meta:
        model = Donation
        fields = ['donor_id']
