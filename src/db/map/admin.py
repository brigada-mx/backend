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


admin.site.register(Locality)
admin.site.register(Submission)
admin.site.register(Organization, OrganizationAdmin)
