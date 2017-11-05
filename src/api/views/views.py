from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, format=None):
    """API root, this view mainly points to list views so that the API
    is discoverable in HATEOAS style.
    """
    return Response({
        'actions': reverse('api:action-list', request=request, format=format),
    })
