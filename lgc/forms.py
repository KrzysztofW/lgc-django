from django import forms
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from .models import Person, Child, ModerationChild, ProcessType
from users import models as user_models
from django.contrib.auth import get_user_model
User = get_user_model()

class PersonCreateForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control'}), label=_('First name'))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control'}), label=_('Last name'))
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'class':'form-control'}))

    passport_expiry = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Passport Expiry'))
    birth_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Birth Date'))
    home_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Home Entity Address'))
    host_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Host Entity Address'))
    HR = forms.ModelMultipleChoiceField(required=False, widget=forms.SelectMultiple(attrs={'class':'form-control'}), queryset=User.objects.filter(role__exact=user_models.HR)|User.objects.filter(role__exact=user_models.HR_ADMIN), label=_('Human Resources'))
    process_name = forms.ModelChoiceField(required=False, queryset=ProcessType.objects.all())
    modified_by = forms.IntegerField(required=False, widget=forms.HiddenInput())
    responsible = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple(attrs={'class':'form-control'}), queryset=user_models.get_local_user_queryset())
    class Meta:
        model = Person
        exclude = ['creation_date'] # XXX

class InitiateAccountForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control'}), label=_('First name'))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control'}), label=_('Last name'))
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'class':'form-control'}))
    responsible = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple(attrs={'class':'form-control'}), queryset=user_models.get_local_user_queryset())
    new_token = forms.BooleanField(required=False, initial=True,
                                   label=_('Send new token'),
                                   help_text=_('Send new authentication token allowing to choose a new password.'))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'language',
                  'responsible', 'new_token', 'is_active']


class InitiateHRForm(InitiateAccountForm):
    is_admin = forms.BooleanField(required=False, label=_('Is admin'),
                                  help_text=_('This HR user can initiate new cases'))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'language', 'company',
                  'responsible', 'new_token', 'is_admin', 'is_active']

class ChildCreateForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    birth_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date', 'class':'form-control', 'style':'width:155px'}), label=_('Birth Date'))
    passport_expiry = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date', 'class':'form-control', 'style':'width:155px'}), label=_('Passport Expiry'))
    passport_nationality = CountryField().formfield(required=False, widget=forms.Select(attrs={'class':'form-control', 'style': 'width:100px'}))

    class Meta:
        model = Child
        exclude = ['parent']

class ModerationChildCreateForm(ChildCreateForm):
    class Meta:
        model = ModerationChild
        exclude = ['parent']

class HREmployeeForm(forms.Form):
    id = forms.CharField(required=True, widget=forms.HiddenInput())
    first_name = forms.CharField(required=True, widget=forms.HiddenInput())
    last_name = forms.CharField(required=True, widget=forms.HiddenInput())
    email = forms.EmailField(required=True, widget=forms.HiddenInput())

class ProcessForm(forms.Form):
    name = forms.ModelChoiceField(queryset=ProcessType.objects.all())
