from django.shortcuts import get_object_or_404

from rest_framework import generics

from db.map.models import Action
from api.serializers import ActionSerializer, ActionLogSerializer


class ActionList(generics.ListAPIView):
    serializer_class = ActionSerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(
            Action.objects.all().order_by('-modified')
        )
        return queryset


class ActionLogList(generics.ListAPIView):
    serializer_class = ActionLogSerializer

    def get_queryset(self):
        action = get_object_or_404(Action, pk=self.kwargs['pk'])
        queryset = self.get_serializer_class().setup_eager_loading(
            action.actionlog_set.all().order_by('-modified')
        )
        return queryset
