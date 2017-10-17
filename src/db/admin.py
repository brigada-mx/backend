from django.contrib import admin

from db.users import StaffUser
from db.models import Locality, LocalityStatisticsLog, Organization, Action
from db.models import ActionLog, Observer, Observation, OrganizationObservation


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
