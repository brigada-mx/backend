import django_filters
from django_filters import rest_framework as filters

from db.map.models import Action, Establishment, Submission
from api.filters import parse_boolean, BooleanFilter


def scian_category_filter(queryset, name, value):
    boolean = parse_boolean(value)
    if boolean is None:
        return queryset
    if boolean is False:
        return queryset.filter(scian_group_id=1)
    return queryset.exclude(scian_group_id=1)


def has_action_filter(queryset, name, value):
    boolean = parse_boolean(value)
    if boolean is None:
        return queryset
    if boolean is False:
        return queryset.filter(action__isnull=True)
    return queryset.filter(action__isnull=False)


class ActionFilter(filters.FilterSet):
    locality_id = django_filters.NumberFilter(name='locality')
    organization_id = django_filters.NumberFilter(name='organization')
    archived = BooleanFilter(name='archived')

    class Meta:
        model = Action
        fields = ['locality_id', 'organization_id', 'archived']


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
    has_action = django_filters.Filter(method=has_action_filter)

    class Meta:
        model = Submission
        fields = ['action_id', 'organization_id', 'published', 'archived']
