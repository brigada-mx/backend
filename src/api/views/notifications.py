from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions
from rest_framework import serializers
from rest_framework import generics

from api import backends
from api import paginators
from message.messengers import get_notifications
from database.nurses.models import NurseUser
from database.staff.models import StaffUser
from database.clients.models import ClientUser


class NotificationSerializer(serializers.Serializer):
    created = serializers.CharField()
    notification = serializers.JSONField()

class FCMNotificationList(generics.ListAPIView):
    """View for returning FCM notifications belonging to the authenticated user.
    These live in redis, not in a relational DB, and aren't associated with any
    Django model.
    """
    serializer_class = NotificationSerializer
    pagination_class = paginators.StandardResultsSetPagination
    authentication_classes = (SessionAuthentication, backends.NurseTokenAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """A list of all FCM notifications for authenticated user. Admin users can
        hit this endpoint to get notifications for any user.
        """
        user = self.request.user
        if user.is_staff:
            pk = self.request.query_params.get('pk', None)
            model = self.request.query_params.get('model', None)
            try:
                user = { "nurse": NurseUser, "staff": StaffUser, "client": ClientUser, }[model].objects.get(pk=pk)
            except:
                return []
            return get_notifications('fcm', user)

        return get_notifications('fcm', user)
