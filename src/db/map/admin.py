from django import forms
from django.contrib.gis import admin

from db.map.models import Locality, Organization, Submission
from db.choices import ORGANIZATION_SECTOR_CHOICES


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = '__all__'

    sector = forms.ChoiceField(choices=ORGANIZATION_SECTOR_CHOICES)


class OrganizationAdmin(admin.ModelAdmin):
    form = OrganizationForm


admin.site.register(Locality)
admin.site.register(Submission)
admin.site.register(Organization, OrganizationAdmin)
