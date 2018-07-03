from typing import Any
import os
import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from api.backends import OrganizationUserAuthentication
from helpers.http import get_s3_client, s3_safe_filename


class GetPresignedUploadUrl(APIView):
    authentication_classes = (OrganizationUserAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs) -> Any:
        bucket = os.getenv('CUSTOM_AWS_STORAGE_BUCKET_NAME')
        s3 = get_s3_client()
        filename = s3_safe_filename(f'{uuid.uuid4()}-{request.data.get("filename", "")}')

        key = f'organization/{request.user.organization.id}/{filename}'
        response = s3.generate_presigned_post(
            Bucket=bucket,
            Key=key,
            Fields={'acl': 'public-read'},
            Conditions=[{'acl': 'public-read'}, ['content-length-range', 10, 1024 * 1024 * 240]],
            ExpiresIn=1800,
        )

        full_url = f'{response["url"]}{key}'
        return Response({**response, 'full_url': full_url}, status=200)
