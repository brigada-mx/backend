from rest_framework.views import APIView
from rest_framework.response import Response

from helpers.db import raw_sql
from helpers.views import DateFilterMixin


class NurseShiftRankings(APIView, DateFilterMixin):
    """Global nurse rankings for gamification =)

    Can be filtered by `start_date` and `end_date`.
    """
    def get(self, request, *args, **kwargs):
        query = """SELECT shift.nurse_id,
                   MAX(nurse.first_name) AS first_name, MAX(nurse.surname) AS surname,
                   EXTRACT (epoch FROM SUM(shift.end - shift.start))/3600 as total_hours,
                   COUNT(shift.id) AS shift_count,
                   MIN(shift.start) AS first_shift
                   FROM reservations_shift AS shift, nurses_nurseuser AS nurse
                   WHERE checkin IS NOT NULL AND checkout IS NOT NULL AND checkout > checkin
                   AND shift.start >= %s AND shift.end < %s
                   AND shift.nurse_id = nurse.asistiabaseuser_ptr_id
                   GROUP BY nurse_id HAVING nurse_id >= 0
                   ORDER BY total_hours DESC LIMIT %s"""

        params = (request.GET.get('start_date', '0001-01-01'),
                  request.GET.get('end_date', '9999-12-12'),
                  request.GET.get('count', '50'),
                  )
        results = raw_sql(query, params)
        for r in results:
            name = "{first_name} {surname}.".format(
                first_name=r['first_name'],
                surname=r['surname'].strip()[:1],
            )
            r['short_name'] = ' '.join(part.capitalize() for part in name.split())
        return Response(results)


