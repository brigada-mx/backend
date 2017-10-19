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
    })
