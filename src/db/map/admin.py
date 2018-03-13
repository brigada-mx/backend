from django import forms
from django.contrib.gis import admin

from db.map.models import Locality, Organization, Submission
from db.choices import ORGANIZATION_SECTOR_CHOICES


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        exclude = ('contact', 'secret_key')

    sector = forms.ChoiceField(choices=ORGANIZATION_SECTOR_CHOICES)


class OrganizationAdmin(admin.ModelAdmin):
    form = OrganizationForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['desc'].initial = '...'
        return form


class SubmissionAdmin(admin.ModelAdmin):
    exclude = ('action', 'published', 'archived', 'desc', 'addr', 'location')
    readonly_fields = ('source', 'source_id', 'submitted', 'image_urls', 'data')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(organization=None)


admin.site.register(Locality)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Organization, OrganizationAdmin)
