from rest_framework import generics

from db.map.models import Action, ActionLog
from api.serializers import ActionSerializer, ActionLogSerializer


class ActionList(generics.ListAPIView):
    serializer_class = ActionSerializer

    def get_queryset(self):
        """Returns a list of all the care log entries assigned to shifts covered by
        the authenticated nurse, or all care log entries if the request comes
        from an admin.
        """
        queryset = self.get_serializer_class().setup_eager_loading(
            Action.objects.all().order_by('-modified')
        )
        return queryset


class ActionLogList(generics.ListAPIView):
    serializer_class = ActionLogSerializer

    def get_queryset(self):
        """Returns a list of all the care log entries assigned to shifts covered by
        the authenticated nurse, or all care log entries if the request comes
        from an admin.
        """
        queryset = self.get_serializer_class().setup_eager_loading(
            ActionLog.objects.filter(action=self.kwargs['pk']).order_by('-modified')
        )
        return queryset
