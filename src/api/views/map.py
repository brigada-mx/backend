import os

from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from raven.contrib.django.raven_compat.models import client
import requests

from db.map.models import State, Municipality, Locality, Action, Organization, Establishment, Submission, Testimonial
from db.map.models import Donor, Donation, VolunteerOpportunity, VolunteerApplication, Share
from db.users.models import VolunteerUser
from api.serializers import StateSerializer, MunicipalitySerializer
from api.serializers import LocalityDetailSerializer, LocalityRawSerializer, LocalitySerializer
from api.serializers import SubmissionSerializer, TestimonialPublicSerializer
from api.serializers import EstablishmentSerializer, ActionMiniSerializer
from api.serializers import ActionSubmissionsSerializer, ActionLogSerializer, ActionDetailSerializer
from api.serializers import ActionLocalityOrganizationSerializer
from api.serializers import OrganizationSerializer, OrganizationDetailSerializer
from api.serializers import DonorSerializer, DonorHasUserSerializer, DonationActionSubmissionsSerializer
from api.serializers import VolunteerOpportunityDetailSerializer, VolunteerUserApplicationCreateSerializer
from api.serializers import ShareSerializer, ShareCreateSerializer, ShareSetUserSerializer, SupportTicketSerializer
from api.paginators import LargeNoCountPagination
from api.throttles import SearchBurstRateScopedThrottle
from api.filters import parse_boolean, ActionFilter, EstablishmentFilter, SubmissionFilter, DonationFilter
from api.filters import VolunteerOpportunityFilter
from jobs.notifications import send_volunteer_application_email
from jobs.messages import send_email
from helpers.http import raise_for_status


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
WHERE map_locality.has_data = true
UNION
SELECT
    map_locality.*,
    (SELECT
        COUNT(*)
        FROM map_action
        WHERE map_action.locality_id = map_locality.id AND map_action.published = true
    ) AS action_count
FROM map_locality
WHERE map_locality.id in (select distinct locality_id from map_action where published = true)"""


class LocalityList(generics.ListAPIView):
    serializer_class = LocalityRawSerializer
    pagination_class = LargeNoCountPagination

    def get_queryset(self):
        return Locality.objects.raw(locality_list_raw_query)


class LocalityWithActionList(generics.ListAPIView):
    serializer_class = LocalitySerializer
    pagination_class = LargeNoCountPagination

    def get_queryset(self):
        return Locality.objects.filter(action__isnull=False).distinct()


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
    ordering_fields = ('created', 'start_date', 'end_date')

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Action.objects.filter(published=True)
        )


class ActionMiniList(generics.ListAPIView):
    serializer_class = ActionMiniSerializer

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
            Submission.objects.filter(
                Q(action__isnull=True) | Q(action__published=True), published=True
            ).exclude(organization=None)
        )


class TestimonialDetail(generics.RetrieveAPIView):
    serializer_class = TestimonialPublicSerializer

    def get_queryset(self):
        return Testimonial.objects.filter(published=True, video__synced=True)


locality_list_search_query = """
SELECT id, cvegeo, location, name, municipality_name, state_name, has_data
FROM locality_search_index
WHERE document @@ to_tsquery('spanish', %s)
ORDER BY ts_rank(document, to_tsquery('spanish', %s)) DESC
LIMIT 50"""


class LocalitySearch(generics.ListAPIView):
    search_burst_throttle_scope = 'search_burst'
    throttle_classes = (SearchBurstRateScopedThrottle,)
    serializer_class = LocalitySerializer

    def get_queryset(self):
        search = self.request.query_params.get('search', '')
        tokens = ' & '.join(search.split())
        tokens = ''.join(ch for ch in tokens if ch.isalnum() or ch in (' ', '&'))
        queryset = Locality.objects.raw(locality_list_search_query, [tokens, tokens])

        has_data = parse_boolean(self.request.query_params.get('has_data'))
        if has_data is None:
            return queryset
        return [l for l in queryset if l.has_data is has_data]


class DonorMiniList(generics.ListAPIView):
    serializer_class = DonorHasUserSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Donor.objects.all()
        )


class DonorList(generics.ListAPIView):
    serializer_class = DonorSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Donor.objects.all()
        )


class DonorDetail(generics.RetrieveAPIView):
    serializer_class = DonorSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Donor.objects.all()
        )


class DonationList(generics.ListAPIView):
    serializer_class = DonationActionSubmissionsSerializer
    filter_class = DonationFilter

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Donation.objects.filter(approved_by_org=True, approved_by_donor=True, action__published=True)
        )


class VolunteerOpportunityDetail(generics.RetrieveAPIView):
    serializer_class = VolunteerOpportunityDetailSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            VolunteerOpportunity.objects.filter(published=True)
        )


class VolunteerOpportunityList(generics.ListAPIView):
    serializer_class = VolunteerOpportunityDetailSerializer
    filter_class = VolunteerOpportunityFilter
    ordering_fields = ('action__score', 'created', 'start_date', 'end_date')

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            VolunteerOpportunity.objects.filter(published=True)
        )


class VolunteerUserApplicationCreate(APIView):
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = VolunteerUserApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        email = serializer.validated_data['email']
        first_name = serializer.validated_data['first_name']
        surnames = serializer.validated_data['surnames']
        age = serializer.validated_data['age']
        opportunity_id = serializer.validated_data['opportunity_id']
        reason_why = serializer.validated_data['reason_why']

        try:
            with transaction.atomic():
                try:
                    user = VolunteerUser.objects.get(email=email)
                except VolunteerUser.DoesNotExist:
                    user = VolunteerUser(email=email)
                user.phone = phone
                user.first_name = first_name
                user.surnames = surnames
                user.age = age
                user.save()

                application = VolunteerApplication.objects.create(
                    opportunity_id=opportunity_id, reason_why=reason_why, user=user
                )
        except Exception as e:
            client.captureException()
            return Response({'error': str(e)}, status=400)
        send_volunteer_application_email.delay(application.id)
        return Response(
            {'user': {'email': email, 'phone': phone, 'first_name': first_name, 'surnames': surnames, 'age': age}}
        )


class ActionShare(APIView):
    def get(self, request, *args, **kwargs):
        action = get_object_or_404(Action.objects.select_related('organization', 'locality'), pk=kwargs['pk'])

        shares = Share.objects.filter(action=action)
        progress = len(shares)
        target = ((progress // 5) + 1) * 5
        try:
            image = action.synced_images(exclude_hidden=True)[0]
        except IndexError:
            image = {}

        action_serializer = ActionLocalityOrganizationSerializer(action)

        email = request.query_params.get('email', '')
        already_shared = False
        if email:
            already_shared = shares.filter(user__email=email).exists()

        return Response(
            {
                'progress': len(shares),
                'target': target,
                'action': action_serializer.data,
                'image': image,
                'already_shared': already_shared,
            },
            status=200,
        )


class ShareListCreate(generics.ListCreateAPIView):
    throttle_scope = 'authentication'

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return ShareCreateSerializer
        return ShareSerializer

    def get_queryset(self):
        return self.get_serializer_class().setup_eager_loading(
            Share.objects.all()
        )


class ShareSetUser(APIView):
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = ShareSetUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        share_id = serializer.validated_data['share_id']

        user = get_object_or_404(VolunteerUser, email=email)
        share = get_object_or_404(Share, id=share_id)
        if share.user:
            return Response({}, status=200)
        share.user = user
        try:
            share.save()
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
        return Response({}, status=200)


class SupportTicketCreate(APIView):
    throttle_scope = 'authentication'

    def post(self, request, *args, **kwargs):
        serializer = SupportTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        phone = serializer.validated_data['phone']
        name = serializer.validated_data['name']
        reason = serializer.validated_data['reason']
        meta = serializer.validated_data['meta']

        body = """Support request from{}:<br><br>
        name: {}<br>
        email: {}<br>
        phone: {}<br><br>
        {}
        """.format(f' {meta}' if meta else '', name, email, phone, reason)

        send_email.delay(
            ['contacto@brigada.mx'],
            f'Support Request - {name}, {email}',
            body,
            'Brigada Support <soporte@brigada.mx>',
        )
        return Response({}, status=200)


class LandingMetrics(APIView):
    def get(self, request, *args, **kwargs):
        groups = (
            Organization.objects.exclude(desc='').count() +
            Donor.objects.filter(donation__isnull=False).distinct().count()
        )
        return Response({
            'groups': groups,
            'actions': Action.objects.filter(published=True).count(),
            'total_spent': Action.objects.filter(published=True).aggregate(t=Sum('budget'))['t']
        }, status=200)


class Landing(APIView):
    def get(self, request, *args, **kwargs):
        action_fields = 'id,locality,organization,donations,action_type,budget,target,unit_of_measurement,preview'
        action_query = f'?level__gte=2&has_start_date=true&ordering=-start_date&page_size=100&fields={action_fields}'
        opportunities_query = '?transparency_level__gte=2&ordering=-created&page_size=100'

        paths = [
            ('metrics', '/landing_metrics/'),
            ('localities', '/localities_with_actions/?page_size=10000'),
            ('opportunities', f'/volunteer_opportunities_cached/{opportunities_query}'),
            ('actions', f'/actions_cached/{action_query}'),
        ]
        data = {}

        for key, path in paths:
            r = requests.get(f'{os.getenv("CUSTOM_API_URL")}{path}')
            raise_for_status(r)
            data[key] = r.json()
        return Response(data, status=200)
