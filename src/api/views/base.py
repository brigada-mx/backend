from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, format=None):
    """API root, ensures the API is discoverable in HATEOAS style.
    """
    return Response({
        'localities': reverse('api:locality-list', request=request, format=format),
        'organizations': reverse('api:organization-list', request=request, format=format),
        'actions': reverse('api:action-list', request=request, format=format),
        'submissions': reverse('api:submission-list', request=request, format=format),
        'donors': reverse('api:donor-list', request=request, format=format),
        'donations': reverse('api:donation-list', request=request, format=format),
    })
