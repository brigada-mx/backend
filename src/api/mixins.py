from collections import namedtuple

from django.db.models.aggregates import Count

from rest_framework.response import Response


class BooleanParamMixin:
    """Sort of explains itself, doesn't it.
    """
    TRUE_STRINGS = ('True', 'true', 'Yes', 'yes',)
    FALSE_STRINGS = ('False', 'false', 'No', 'no',)

    @classmethod
    def parse_boolean(cls, param):
        if param in cls.TRUE_STRINGS:
            return True
        if param in cls.FALSE_STRINGS:
            return False
        return None


class EagerLoadingMixin:
    @classmethod
    def setup_eager_loading(cls, queryset):
        # foreign key and one to one
        if hasattr(cls, "_SELECT_RELATED_FIELDS"):
            queryset = queryset.select_related(*cls._SELECT_RELATED_FIELDS)
        # many to many, many to one
        if hasattr(cls, "_PREFETCH_RELATED_FIELDS"):
            queryset = queryset.prefetch_related(*cls._PREFETCH_RELATED_FIELDS)
        # each element in this list must be a function that returns a `Prefetch` instance
        if hasattr(cls, "_PREFETCH_FUNCTIONS"):
            queryset = queryset.prefetch_related(*[func() for func in cls._PREFETCH_FUNCTIONS])
        return queryset


class DynamicFieldsMixin:
    """A serializer mixin that takes an additional `fields` argument that controls
    which fields are included in an object's serialized representation.
    Usage:
        class MySerializer(DynamicFieldsMixin, serializers.ModelSerializer):

    Gotcha: a serializer can't inherit from this mixin if it also inherits from
    a superclass that uses the mixin.

    Taken from: https://gist.github.com/dbrgn/4e6fc1fe5922598592d6
    """
    def __init__(self, *args, **kwargs):
        super(DynamicFieldsMixin, self).__init__(*args, **kwargs)
        if not self.context:
            return
        fields = self.context['request'].query_params.get('fields')
        if fields:
            fields = fields.split(',')
            # drop any fields that are not specified in the `fields` argument
            allowed = set(fields)
            existing = set(self.fields.keys())
            # remove fields that are in `existing` but not in `allowed`
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class MetricsMixin(BooleanParamMixin):
    """Mixin for API views that returns filtered counts, unfiltered base counts,
    and rates obtained from these counts. Handles grouping and "zipping" of
    filtered/unfiltered result sets.

    Optional `__min_count__` query param will return only results whose counts
    exceed a certain value. Response conforms to structure of a typical
    `ListAPIView` response.
    """
    FILTER_PARAMS = ()
    GROUP_BY_PARAMS = ()

    def get(self, request, *args, **kwargs):
        """Gets filtered queryset, then unfiltered queryset, by removing
        `FILTER_PARAMS` from `request.GET` and "replaying" request.
        """
        self.MIN_COUNT = int(request.GET.get('__min_count__', 0))

        qs = self._get_queryset(*args, **kwargs)

        GET = request.GET
        GET_BASE = request.GET.copy()
        for param in self.FILTER_PARAMS:
            GET_BASE.pop(param, None)  # remove filter params from `request.GET`
        self.request._request.GET = GET_BASE  # modify `request.GET`
        qs_base = self._get_queryset(*args, **kwargs)

        rates = self._compute_rates(qs, qs_base)
        response = {'params': dict(GET),
                    'params_base': dict(GET_BASE),
                    'count': rates.count,
                    'results': rates.results}
        return Response(response)

    def _get_queryset(self, *args, **kwargs):
        self._group_by_fields = []  # set this on instance for use in `_compute_rates`
        for group_by_param in self.GROUP_BY_PARAMS:
            if self.parse_boolean(self.request.GET.get(group_by_param[0])):
                self._group_by_fields.append(group_by_param[1])

        qs = self.filter_queryset(self.get_queryset())
        if self._group_by_fields:
            return qs.values(*self._group_by_fields).order_by(*self._group_by_fields).annotate(total=Count('id'))
        else:
            return [{'total': qs.count()}]

    def _compute_rates(self, qs, qs_base):
        """Zips filtered/unfiltered result sets together and calculates rates.
        """
        counts = list(qs)
        base_counts = list(qs_base)
        rates = []

        idx = 0
        for bc in list(base_counts):
            group_by_fields_dict = {field: bc[field] for field in self._group_by_fields}
            base_rate = {'count': 0, 'base_count': bc['total'], 'rate': 0}

            try:
                c = counts[idx]
            except IndexError:
                base_rate.update(group_by_fields_dict)
                rates.append(base_rate)
                continue

            for field in self._group_by_fields:
                if c[field] != bc[field]:
                    base_rate.update(group_by_fields_dict)
                    rates.append(base_rate)
                    break
            else:
                assert c['total'] <= bc['total']
                # this sanity check is almost guaranteed to fail if
                # iteration between the querysets gets out of phase
                rate = {'count': c['total'], 'base_count': bc['total'],
                        'rate': c['total'] / bc['total'] if bc['total'] != 0 else None}
                rate.update(group_by_fields_dict)
                rates.append(rate)
                idx += 1

        Rates = namedtuple('Rates', 'count, results')  # conforms with typical response from a `ListAPIView`
        if self.MIN_COUNT > 0:
            rates = [r for r in rates if r['count'] >= self.MIN_COUNT]
        return Rates(len(rates), rates)
