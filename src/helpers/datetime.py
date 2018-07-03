from datetime import datetime, timedelta
from pytz import NonExistentTimeError, AmbiguousTimeError  # type: ignore

from django.utils import timezone


def local_date(offset=0):
    """Return the local date plus `offset` days.
    """
    return timezone.localtime(timezone.now()).date() + timedelta(days=offset)


def make_aware_safe(dt):
    """Avoids the biannual pair of `pytz.NonExistentTimeError` and
    `pytz.AmbiguousTimeError` exceptions.

    http://www.ilian.io/django-pytz-nonexistenttimeerror-and-ambiguoustimeerror/
    """
    if timezone.is_aware(dt):
        return dt
    try:
        return timezone.make_aware(dt)
    except (NonExistentTimeError, AmbiguousTimeError):
        return timezone.make_aware(dt + timedelta(hours=1))


def strptime_aware(datestring, format):
    """Makes sure datetime returned by strptime is timezone aware.

    https://docs.python.org/3.5/library/datetime.html
    """
    return make_aware_safe(datetime.strptime(datestring, format))


def timediff(t1=None, t0=None, fmt='h'):
    """Calculate the time difference between `t1` and `t0`, timezone aware
    `datetime` objects, in various fmts.

    Doesn't account for leap years, because this doesn't matter at all, and it
    turns out it's really hard!
    http://stackoverflow.com/questions/4436957/pythonic-difference-between-two-dates-in-years
    """
    def clean(dt):
        if not dt:
            return timezone.now()
        return make_aware_safe(dt)

    fmts = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'y': 31536000}
    t1 = clean(t1)
    t0 = clean(t0)
    return (t1 - t0).total_seconds() / fmts[fmt]
