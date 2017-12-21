from django.db.models.aggregates import Count

import django_filters


class RelatedObjectsCountFilter(django_filters.Filter):
    """Are there l.t. or g.t. `N` objects related to objects in queryset?
    """
    def __init__(self, *args, **kwargs):
        self._lookup_expr = kwargs.pop('lookup_expr', 'exact')
        self._model = kwargs.pop('model')
        return super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value not in (None, ''):
            pks = qs.annotate(_num_objects=Count(self.name)).filter(
                **{'{}__{}'.format('_num_objects', self._lookup_expr): value}
            ).values_list('pk', flat=True)
            return self._model.objects.filter(pk__in=pks)
        return qs

