from rest_framework.views import APIView
from rest_framework.response import Response

from raven.contrib.django.raven_compat.models import client
from db.map.models import DiscourseUser, DiscoursePostEvent
from jobs.kobo import sync_submission


class KoboSubmissionWebhook(APIView):
    def post(self, request):
        try:
            sync_submission(request.data)
        except Exception as e:
            client.captureException()
            return Response({'error': str(e)}, status=400)
        else:
            return Response(request.data)


class DiscourseEventWebhook(APIView):
    def post(self, request):
        try:
            if 'user' in request.data:
                DiscourseUser.save_from_webhook(request.data)
            elif 'post' in request.data:
                DiscoursePostEvent.save_from_webhook(request.data)
        except Exception as e:
            client.captureException()
            return Response({'error': str(e)}, status=400)
        else:
            return Response(request.data)
