from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError as ValidationErrorDjango

from rest_framework.serializers import ValidationError as ValidationErrorRest
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from api.helpers import error_response_json


def custom_exception_handler(exc, context):
    # call rest framework's default exception handler first to get the standard error response
    response = exception_handler(exc, context)

    if isinstance(exc, IntegrityError):
        return Response(
            error_response_json(
                str(exc.args),
                'Algo salió mal. Es posible que ya tienes un objeto con el mismo nombre o el mismo valor.',
                error_type='integrity_error',
                dump_to_string=False),
            status=status.HTTP_400_BAD_REQUEST)
    return response


class ValidationError(ValidationErrorRest, ValidationErrorDjango):
    pass
