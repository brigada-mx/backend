import django_filters
from django_filters import rest_framework as filters

from db.map.models import Action, Establishment, Submission
from api.filters import parse_boolean


def scian_category_filter(queryset, name, value):
    boolean = parse_boolean(value)
    if boolean is None:
        return queryset
    if boolean is False:
        return queryset.filter(scian_group_id=1)
    return queryset.filter(scian_group_id__gt=1)


class ActionFilter(filters.FilterSet):
    locality_id = django_filters.NumberFilter(name='locality')
    organization_id = django_filters.NumberFilter(name='organization')

    class Meta:
        model = Action
        fields = ['locality_id', 'organization_id']


class EstablishmentFilter(filters.FilterSet):
    locality_id = django_filters.NumberFilter(name='locality')
    is_categorized = django_filters.Filter(method=scian_category_filter)

    class Meta:
        model = Establishment
        fields = ['locality_id']


class SubmissionFilter(filters.FilterSet):
    action_id = django_filters.NumberFilter(name='action')

    class Meta:
        model = Submission
        fields = ['action_id']
