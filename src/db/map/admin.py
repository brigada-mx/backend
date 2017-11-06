from django.contrib.gis import admin

from db.map.models import Locality, Organization, Action, ActionLog
from db.map.models import Observer, Observation, OrganizationObservation


admin.site.register(Locality)
admin.site.register(Organization)
admin.site.register(Action)
admin.site.register(ActionLog)
admin.site.register(Observer)
admin.site.register(Observation)
admin.site.register(OrganizationObservation)
