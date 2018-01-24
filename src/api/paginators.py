import sys
from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class NoCountPagination(LimitOffsetPagination):
    """Ensures Django doesn't call `count` on queryset, because counting records
    in large tables can be very expensive, especially with PostgreSQL.
    """
    default_limit = 100
    limit_query_param = 'page_size'
    max_limit = 2000

    def paginate_queryset(self, queryset, request, view=None):
        # https://github.com/encode/django-rest-framework/blob/master/rest_framework/pagination.py
        self.count = sys.maxsize
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        return list(queryset[self.offset:self.offset + self.limit])

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class LargeNoCountPagination(NoCountPagination):
    max_limit = 20000
