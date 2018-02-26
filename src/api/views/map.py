from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404

from rest_framework import generics

from db.map.models import State, Municipality, Locality, Action, Organization, Establishment, Submission
from api.serializers import StateSerializer, MunicipalitySerializer
from api.serializers import LocalityDetailSerializer, LocalityRawSerializer, LocalitySearchSerializer
from api.serializers import EstablishmentSerializer, SubmissionSerializer
from api.serializers import ActionSubmissionsSerializer, ActionLogSerializer, ActionDetailSerializer
from api.serializers import OrganizationSerializer, OrganizationDetailSerializer
from api.paginators import LargeNoCountPagination
from api.throttles import SearchBurstRateScopedThrottle
from api.filters import ActionFilter, EstablishmentFilter, SubmissionFilter


class StateList(generics.ListAPIView):
    serializer_class = StateSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            State.objects.all()
        )


class MunicipalityList(generics.ListAPIView):
    serializer_class = MunicipalitySerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Municipality.objects.all()
        )


locality_list_raw_query = """
SELECT
    map_locality.*,
    (SELECT
        COUNT(*)
        FROM map_action
        WHERE map_action.locality_id = map_locality.id AND map_action.published = true
    ) AS action_count
FROM map_locality
WHERE map_locality.has_data = true"""


class LocalityList(generics.ListAPIView):
    serializer_class = LocalityRawSerializer
    pagination_class = LargeNoCountPagination

    def get_queryset(self):
        return Locality.objects.raw(locality_list_raw_query)


class LocalityDetail(generics.RetrieveAPIView):
    serializer_class = LocalityDetailSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Locality.objects.all().order_by('-modified')
        )


class EstablishmentList(generics.ListAPIView):
    serializer_class = EstablishmentSerializer
    filter_class = EstablishmentFilter

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Establishment.objects.all()
        )


class ActionList(generics.ListAPIView):
    serializer_class = ActionSubmissionsSerializer
    filter_class = ActionFilter

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Action.objects.filter(published=True)
        )


class ActionDetail(generics.RetrieveAPIView):
    serializer_class = ActionDetailSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Action.objects.filter(published=True)
        )


class ActionLogList(generics.ListAPIView):
    serializer_class = ActionLogSerializer

    def get_queryset(self):
        action = get_object_or_404(Action, pk=self.kwargs['pk'], published=True)
        return self.get_serializer_class().setup_eager_loading(
            action.actionlog_set.all().order_by('-modified')
        )


class OrganizationList(generics.ListAPIView):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Organization.objects.all().order_by('-modified')
        )


class OrganizationDetail(generics.RetrieveAPIView):
    serializer_class = OrganizationDetailSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Organization.objects.all().order_by('-modified')
        )


class SubmissionList(generics.ListAPIView):
    serializer_class = SubmissionSerializer
    filter_class = SubmissionFilter

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Submission.objects.filter(Q(action__isnull=True) | Q(action__published=True), published=True)
        )


locality_list_search_query = """
SELECT id, cvegeo, location, name, municipality_name, state_name
FROM locality_search_index
WHERE document @@ to_tsquery('spanish', '{tokens}')
ORDER BY ts_rank(document, to_tsquery('spanish', '{tokens}')) DESC
LIMIT 30"""


class LocalitySearch(generics.ListAPIView):
    search_burst_throttle_scope = 'search_burst'
    throttle_classes = (SearchBurstRateScopedThrottle,)

    serializer_class = LocalitySearchSerializer

    def get_queryset(self):
        search = self.request.query_params.get('search', '')
        tokens = ' & '.join(search.split())
        return Locality.objects.raw(locality_list_search_query.format(tokens=tokens))
