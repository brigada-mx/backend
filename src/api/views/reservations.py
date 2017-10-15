from rest_framework import generics

from api.serializers import ReservationDetailSerializer, ReservationSerializer
from api import backends
from database.reservations.models import Reservation

from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication


class ReservationList(generics.ListAPIView):
    """Read only view for reservation details, available only to client.
    """
    authentication_classes = (SessionAuthentication, backends.ClientTokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.auth == "ClientUser":
            return ReservationDetailSerializer
        return ReservationSerializer

    def get_queryset(self):
        """Returns a list of reservations, or just the client's reservation.
        """
        queryset = Reservation.objects.all()
        if self.request.auth == "ClientUser":
            return queryset.filter(clientuser=self.request.user).distinct()
        return queryset


class ReservationDetail(generics.RetrieveUpdateAPIView):
    """Retrieve details for reservation, or update reservation.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
