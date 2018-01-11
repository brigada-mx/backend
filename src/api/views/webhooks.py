from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from jobs.kobo import sync_submission


class KoboSubmissionWebhook(APIView):
    def post(self, request):
        try:
            sync_submission(request.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(request.data)
