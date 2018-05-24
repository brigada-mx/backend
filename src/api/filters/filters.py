import django_filters


def parse_boolean(boolean):
    if boolean in ('True', 'true'):
        return True
    if boolean in ('False', 'false'):
        return False
    return None


class BooleanFilter(django_filters.Filter):
    def filter(self, qs, value):
        boolean = parse_boolean(value)
        if boolean is None:
            return qs
        return qs.filter(**{self.name: boolean})
