import django_filters
from django_filters import rest_framework as filters

from db.map.models import Action


class ActionFilter(filters.FilterSet):
    """Filter `NurseUser`s by all kinds of attributes.
    """
    locality_id = django_filters.NumberFilter(name='locality')
    organization_id = django_filters.NumberFilter(name='organization')

    class Meta:
        model = Action
        fields = ['locality_id', 'organization_id']
