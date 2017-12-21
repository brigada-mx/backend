from django.shortcuts import get_object_or_404

from rest_framework import generics

from db.map.models import State, Municipality, Locality, Action, Organization
from api.serializers import StateSerializer, MunicipalitySerializer, LocalitySerializer
from api.serializers import ActionSerializer, ActionLogSerializer, OrganizationSerializer


class StateList(generics.ListAPIView):
    serializer_class = StateSerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(
            State.objects.all()
        )
        return queryset


class MunicipalityList(generics.ListAPIView):
    serializer_class = MunicipalitySerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(
            Municipality.objects.all()
        )
        return queryset


class LocalityList(generics.ListAPIView):
    serializer_class = LocalitySerializer
    filter_fields = ('has_data', 'cvegeo')

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(
            Locality.objects.all().order_by('-modified')
        )
        return queryset


class LocalityDetail(generics.RetrieveAPIView):
    serializer_class = LocalitySerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(
            Locality.objects.all().order_by('-modified')
        )
        return queryset


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


class OrganizationList(generics.ListAPIView):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(
            Organization.objects.all().order_by('-modified')
        )
        return queryset


class OrganizationDetail(generics.RetrieveAPIView):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        queryset = self.get_serializer_class().setup_eager_loading(
            Organization.objects.all().order_by('-modified')
        )
        return queryset
