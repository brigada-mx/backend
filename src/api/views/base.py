from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, format=None):
    """API root, ensures the API is discoverable in HATEOAS style.
    """
    return Response({
        'swagger.json': reverse('api:schema-json', request=request, format=format, kwargs={'format': '.json'}),
        'swagger.yaml': reverse('api:schema-json', request=request, format=format, kwargs={'format': '.yaml'}),
        'swagger-ui': reverse('api:schema-swagger-ui', request=request, format=format),
        'redoc': reverse('api:schema-redoc', request=request, format=format),
        'localities': reverse('api:locality-list', request=request, format=format),
        'organizations': reverse('api:organization-list', request=request, format=format),
        'actions': reverse('api:action-list', request=request, format=format),
        'submissions': reverse('api:submission-list', request=request, format=format),
        'donors': reverse('api:donor-list', request=request, format=format),
        'donations': reverse('api:donation-list', request=request, format=format),
    })
