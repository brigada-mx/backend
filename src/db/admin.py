from django.contrib import admin

from db.users.models import StaffUser
from db.map.models import Locality, Organization, Action, ActionLog, Submission


class UserAdmin(admin.ModelAdmin):
    exclude = ('password',)
    readonly_fields = ('password',)


user_models = (
    StaffUser,
)
models = (
    Locality,
    Organization,
    Action,
    ActionLog,
    Submission,
)

admin.site.register(user_models, UserAdmin)
admin.site.register(models)
