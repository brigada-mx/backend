from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication

from api import backends


@api_view(['GET'])
@authentication_classes((SessionAuthentication, backends.NurseTokenAuthentication,))
@permission_classes((permissions.IsAuthenticated,))
def api_root(request, format=None):
    """API root, this view mainly points to list views so that the API
    is discoverable in HATEOAS style.
    """
    return Response({
        'nurse account connection': reverse('api:invite', request=request, format=format),
        'nurse account connection accept': reverse('api:accept', request=request, format=format),

        'nurse auth': reverse('api:nurse-auth', request=request, format=format),
        'nurses': reverse('api:nurse-list', request=request, format=format),
        'nurse care schedule tasks': reverse('api:nursecarescheduletask-list', request=request, format=format),

        'nurse reviews': reverse('api:nursereview-list', request=request, format=format),

        'clients': reverse('api:client-list', request=request, format=format),

        'reservations': reverse('api:reservation-list', request=request, format=format),

        'activity feed': reverse('api:activityfeeditem-list', request=request, format=format),

        'shifts': reverse('api:shift-list', request=request, format=format),
        'shifts unprotected': reverse('api:shift-unprotected-list', request=request, format=format),
        'shift incidents': reverse('api:shiftincident-list', request=request, format=format),

        'shift schedules': reverse('api:shiftschedule-list', request=request, format=format),
        'shift posting responses': reverse('api:shiftschedulepostingresponse-list', request=request, format=format),
        'shift schedule days': reverse('api:shiftscheduleday-list', request=request, format=format),

        'care schedules': reverse('api:careschedule-list', request=request, format=format),

        'care log entries': reverse('api:carelogentry-list', request=request, format=format),
        'patients': reverse('api:patient-list', request=request, format=format),
        'care circle members': reverse('api:care-circle-member-list', request=request, format=format),

        'notifications': reverse('api:notification-list-fcm', request=request, format=format),

        'metrics care log entries': reverse('api:metrics-carelogentry', request=request, format=format),
        'metrics shifts': reverse('api:metrics-shifts', request=request, format=format),
        'metrics posting responses': reverse('api:metrics-posting-responses', request=request, format=format),
        'metrics nurses': reverse('api:metrics-nurses', request=request, format=format),
        'metrics nurse reviews': reverse('api:metrics-nurse-reviews', request=request, format=format),
        'metrics clients': reverse('api:metrics-clients', request=request, format=format),
    })
