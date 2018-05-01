import os
import hmac
import hashlib

from rest_framework.views import APIView
from rest_framework.response import Response

from raven.contrib.django.raven_compat.models import client
from db.map.models import DiscourseUser, DiscoursePostEvent, DiscourseTopicEvent
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
        event_signature = request.META.get('HTTP_X_DISCOURSE_EVENT_SIGNATURE')
        event_type = request.META.get('HTTP_X_DISCOURSE_EVENT_TYPE', '')
        event = request.META.get('HTTP_X_DISCOURSE_EVENT', '')

        if not event_signature:
            client.captureMessage('discourse_webhook_no_signature')
            return Response({'error': 'discourse_webhook_no_signature'}, status=400)
        signature = hmac.new(
            str.encode(os.getenv('CUSTOM_DISCOURSE_WEBHOOK_SECRET')), request.body, digestmod=hashlib.sha256
        ).hexdigest()
        if f'sha256={signature}' != event_signature:
            client.captureMessage('discourse_webhook_incorrect_signature')
            return Response({'error': 'discourse_webhook_incorrect_signature'}, status=400)

        try:
            if event_type == 'user':
                DiscourseUser.save_from_webhook(request.data)
            elif event_type == 'post':
                DiscoursePostEvent.save_from_webhook(request.data, event)
            elif event_type == 'topic':
                DiscourseTopicEvent.save_from_webhook(request.data, event)
        except Exception as e:
            client.captureException()
            return Response({'error': str(e)}, status=400)
        else:
            return Response(request.data)
