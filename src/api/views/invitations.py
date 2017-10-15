from rest_framework import views
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication

from django.utils import timezone
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.conf import settings

from database.nurses.models import NurseReservationConnection
from api import backends
from api.serializers import DeviceSerializer


INVITE_MESSAGE_MOBILE = """Hola! Esta es una invitación para conectarnos en la app Asistia. Da clic aquí:
{}

O si prefieres, copia y pega este código en tu app, en la sección de cuenta:
{}"""

INVITE_MESSAGE_WEB = "Hola! Esta es una invitación para conectarnos en la app Asistia. Da clic aquí:%0D%0A{}%0D%0A%0D%0AO si prefieres, copia y pega este código en tu app, en la sección de cuenta:%0D%0A{}"

class CreateNurseReservationConnection(views.APIView):
    authentication_classes = (backends.NurseTokenAuthentication, backends.UnauthenticatedNurse, backends.ClientTokenAuthentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = DeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.validated_data.get('device', 'mobile')
        invite_message = INVITE_MESSAGE_MOBILE if device == 'mobile' else INVITE_MESSAGE_WEB

        nurse, reservation = None, None

        if request.user.is_client:
            invited_by = 0
            reservation = request.user.reservation
            login_url = reverse('login', kwargs={'user_type': 'cuidadores'})
        if request.user.is_nurse:
            invited_by = 1
            nurse = request.user
            login_url = reverse('login', kwargs={'user_type': 'clientes'})

        connection = NurseReservationConnection.objects.create(
            nurse=nurse,
            reservation=reservation,
            invited_by=invited_by
        )

        accept_url = "{}{}?next={}?token={}".format(
            settings.SITE_URL,
            login_url,
            reverse('api:accept'),
            connection.token,
        )

        return Response({
            'token': connection.token,
            'url': accept_url,
            'message': invite_message.format(accept_url, connection.token)
        })


class AcceptNurseReservationConnection(views.APIView):
    authentication_classes = (backends.NurseTokenAuthentication, backends.ClientTokenAuthentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """Even though this is an "unsafe" view, it responds to GET so it can
        by hit simply clicking on a link. It responds with a redirect.
        """
        self.get_connection(request.user, request.query_params.get('token', None))
        if request.user.is_client:
            return redirect(reverse('clients:home'))
        if request.user.is_nurse:
            return redirect(reverse('nurses:home'))
        return redirect(reverse('landing'))

    def post(self, request, *args, **kwargs):
        """Clients of the API should hit this endpoint with a POST request.
        """
        connection = self.get_connection(request.user, request.data.get('token', None))
        return Response({'accepted': connection.accepted})

    @classmethod
    def get_connection(cls, user, token):
        if not token: # no blank tokens allowed, just in case `set_token` failed when connection was created
            raise Http404()
        connection = get_object_or_404(NurseReservationConnection, token=token)

        if user.is_client and not connection.reservation:
            connection.reservation = user.reservation
            connection.accepted = timezone.now()
            connection.save()
            connection.assign_nurse_shift_days()
        if user.is_nurse and not connection.nurse:
            connection.nurse = user
            connection.accepted = timezone.now()
            connection.save()
            connection.assign_nurse_shift_days()
        return connection

