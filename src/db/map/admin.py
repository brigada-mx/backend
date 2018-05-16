from django import forms
from django.contrib.gis import admin

from db.map.models import Locality, Organization, Submission, Donor
from db.choices import ORGANIZATION_SECTOR_CHOICES


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        exclude = ('contact', 'secret_key', 'accepting_help', 'help_desc')

    sector = forms.ChoiceField(choices=ORGANIZATION_SECTOR_CHOICES)


class OrganizationAdmin(admin.ModelAdmin):
    form = OrganizationForm


class SubmissionAdmin(admin.ModelAdmin):
    exclude = ('action', 'published', 'archived', 'desc', 'addr', 'location')
    readonly_fields = ('source', 'source_id', 'submitted', 'images', 'data')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(organization=None)


admin.site.register(Locality)
admin.site.register(Donor)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Organization, OrganizationAdmin)
