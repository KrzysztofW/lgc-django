from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import Person

class PersonCreateForm(forms.ModelForm):
    passeport_expiry = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Passeport Expiry'))
    work_authorization_start = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Work Authorization Start Date'))
    work_authorization_end = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Work Authorization End Date'))
    residence_permit_start = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Residence Permit Start Date'))
    residence_permit_end = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Residence Permit End Date'))
    birth_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Birth Date'))
    home_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Home Entity Address'))
    host_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Host Entity Address'))

    class Meta:
        model = Person
        exclude = ['creation_date']
