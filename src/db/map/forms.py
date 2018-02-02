from django import forms

from db.map.models import Organization
from db.choices import ORGANIZATION_SECTOR_CHOICES


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = '__all__'

    sector = forms.ChoiceField(choices=ORGANIZATION_SECTOR_CHOICES)
