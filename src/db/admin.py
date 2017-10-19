from django.contrib import admin

from db.users.models import StaffUser
from db.map.models import Locality, LocalityStatisticsLog, Organization, Action
from db.map.models import ActionLog, Observer, Observation, OrganizationObservation


class UserAdmin(admin.ModelAdmin):
    exclude = ('password',)
    readonly_fields = ('password',)


user_models = (
    StaffUser,
)
models = (
    Locality,
    LocalityStatisticsLog,
    Organization,
    Action,
    ActionLog,
    Observer,
    Observation,
    OrganizationObservation,
)

admin.site.register(user_models, UserAdmin)
admin.site.register(models)
