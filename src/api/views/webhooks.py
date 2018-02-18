from rest_framework.views import APIView
from rest_framework.response import Response

from jobs.kobo import sync_submission


class KoboSubmissionWebhook(APIView):
    def post(self, request):
        try:
            sync_submission(request.data)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        else:
            return Response(request.data)
