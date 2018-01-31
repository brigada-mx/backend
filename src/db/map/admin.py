from django.contrib.gis import admin

from db.map.models import Locality, Organization, Submission
from web.forms import OrganizationForm


class OrganizationAdmin(admin.ModelAdmin):
    form = OrganizationForm


admin.site.register(Locality)
admin.site.register(Submission)
admin.site.register(Organization, OrganizationAdmin)
