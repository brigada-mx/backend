import json

from django.utils import timezone
from django.db.models import Q
from django.db.models.aggregates import Count

import django_filters
from rest_framework import exceptions

from api.mixins import BooleanParamMixin
from helpers.datetime import strptime_aware


def WITHIN_DAYS_Q(lower_field='end__gt', lower_days=5,
                  upper_field='start__lt', upper_days=15):
    """Returns a `Q` instance for filtering a queryset based on a `datetime`
    field's proximity to the current moment minus or plus some number of days.

    By default it only retains objects that have `end`ed with the last 5 days or
    will `start` within the next 15 days.
    """
    return Q(**{lower_field: timezone.now() - timezone.timedelta(days=lower_days),
                upper_field: timezone.now() + timezone.timedelta(days=upper_days)})


class BooleanFilter(django_filters.Filter, BooleanParamMixin):

    def filter(self, qs, value):
        boolean = self.parse_boolean(value)
        if boolean is None:
            return qs
        return qs.filter(
            **{ self.name: boolean }
        )


class NotNullFilter(django_filters.Filter, BooleanParamMixin):

    def filter(self, qs, value):
        is_null = self.parse_boolean(value)
        if is_null is None:
            return qs
        return qs.exclude(
            **{ '{}__{}'.format(self.name, 'isnull'): is_null }
        )


class NotZeroOrNullFilter(django_filters.Filter, BooleanParamMixin):

    def filter(self, qs, value):
        boolean = self.parse_boolean(value)
        if boolean is None:
            return qs
        filter_function = 'exclude' if boolean == True else 'filter'
        return qs.__getattribute__(filter_function)(
            Q(**{ self.name: 0 }) | Q(**{ '{}__isnull'.format(self.name): True })
        )


class HasStringFilter(django_filters.Filter, BooleanParamMixin):

    def filter(self, qs, value):
        boolean = self.parse_boolean(value)
        if boolean is None:
            return qs
        filter_function = 'exclude' if boolean == True else 'filter'
        return qs.__getattribute__(filter_function)(
            **{ self.name: '' }
        )


class HasListFilter(django_filters.Filter, BooleanParamMixin):
    """For PostgreSQL `ArrayField`.
    """
    def filter(self, qs, value):
        boolean = self.parse_boolean(value)
        if boolean is None:
            return qs
        filter_function = 'exclude' if boolean == True else 'filter'
        return qs.__getattribute__(filter_function)(
            **{ self.name: '{}' }
        )


class NumberMultipliedByFilter(django_filters.NumberFilter):
    """Like NumberFilter, but `value` passed in filter is multiplied by
    `multiplied_by` arg.

    For example, for converting a seconds filter to a minutes filter, this class
    can be instantiated with `multiplied_by=60`.
    """
    def __init__(self, *args, **kwargs):
        self._multiplied_by = kwargs.pop('multiplied_by', 1)
        return super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        return qs.filter(
            **{ '{}__{}'.format(self.name, self.lookup_expr): value * self._multiplied_by }
        )


class DateRangeFilter(django_filters.Filter):
    """Like NumberFilter, but `value` passed in filter is multiplied by
    `multiplied_by` arg.

    For example, for converting a seconds filter to a minutes filter, this class
    can be instantiated with `multiplied_by=60`.
    """
    def _parse_date_param(self, date, fmt='%Y-%m-%d'):
        try:
            date = strptime_aware(date, fmt)
        except:
            raise exceptions.ParseError("Value `{}` is not a valid date range.".format(date))
        return date

    def filter(self, qs, value):
        date_strings = value.split(',')
        if len(date_strings) != 2:
            raise exceptions.ParseError("Value `{}` is not a valid date range.".format(value))

        min_date, max_date = self._parse_date_param(date_strings[0]), self._parse_date_param(date_strings[1])
        return qs.filter(
            **{ '{}__gte'.format(self.name): min_date, '{}__lt'.format(self.name): max_date }
        )


class ListFilter(django_filters.Filter):
    """Parses a comma-separted list from querystring and returns records for which
    the named field is `in` this list.

    Pass `exclude = True` to constructor to filter for integers `not in` list.
    """
    MAX_FILTER_LENGTH = 500 # max length of integer list string that will be parsed from querystring

    def __init__(self, *args, **kwargs):
        exclude = kwargs.pop('exclude', False)
        self.filter_function = 'exclude' if exclude == True else 'filter'
        return super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value not in (None, ''):
            try:
                values = json.loads(value)
            except:
                raise exceptions.ParseError("Value `{}` passed for `{}` could not be parsed.".format(value, self.name))
            if not isinstance(values, list):
                raise exceptions.ParseError("Value `{}` passed for `{}` is not a list, make sure it is wrapped in brackets.".format(value, self.name))

            if values: # don't filter if list is empty
                return qs.__getattribute__(self.filter_function)(
                    **{ '{}__{}'.format(self.name, 'in'): values }
                )
        return qs


class RelatedObjectsCountFilter(django_filters.Filter):
    """Are there l.t. or g.t. `N` objects related to objects in queryset.
    """
    def __init__(self, *args, **kwargs):
        self._lookup_expr = kwargs.pop('lookup_expr', 'exact')
        self._model = kwargs.pop('model')
        return super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value not in (None, ''):
            pks = qs.annotate(_num_objects=Count(self.name)).filter(
                **{ '{}__{}'.format('_num_objects', self._lookup_expr): value }
            ).values_list('pk', flat=True)
            return self._model.objects.filter(pk__in=pks)
        return qs
