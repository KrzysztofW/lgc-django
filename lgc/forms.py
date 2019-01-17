from django.forms import inlineformset_factory
from django.forms import modelformset_factory
from django import forms
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from .models import Person, Child

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

class ChildCreateForm(forms.ModelForm):
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    birth_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date', 'class':'form-control', 'style':'width:155px'}), label=_('Birth Date'))
    passeport_expiry = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date', 'class':'form-control', 'style':'width:155px'}), label=_('Passeport Expiry'))
    passeport_nationality = CountryField().formfield(required=False, widget=forms.Select(attrs={'class':'form-control', 'style': 'width:100px'}))

    class Meta:
        model = Child
        exclude = ['person']
