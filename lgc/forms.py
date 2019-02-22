from django import forms
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from .models import Person, Child, ModerationChild, HR
from django.contrib.auth.models import User

class PersonCreateForm(forms.ModelForm):
    passport_expiry = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Passport Expiry'))
    work_authorization_start = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Work Authorization Start Date'))
    work_authorization_end = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Work Authorization End Date'))
    birth_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}), label=_('Birth Date'))
    home_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Home Entity Address'))
    host_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Host Entity Address'))
    HR = forms.ModelMultipleChoiceField(required=False, widget=forms.SelectMultiple(attrs={'class':'form-control'}), queryset=HR.objects.all(), label=_('Human Resources'))
    company = forms.CharField(required=False, label=_('Company'))

    class Meta:
        model = Person
        exclude = ['creation_date']

class InitiateCaseForm(forms.ModelForm):
    LANG_CHOICES = (
        ('FR', _("French")),
        ('EN', _("English")),
    )
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control'}), label=_('First name'))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control'}), label=_('Last name'))
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'class':'form-control'}))
    language = forms.ChoiceField(widget=forms.Select(attrs={'class':'form-control'}),
                                 choices=LANG_CHOICES, label=_('Language'))
    responsible = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple(attrs={'class':'form-control'}), queryset=User.objects.all())
    new_token = forms.BooleanField(required=False, initial=True,
                                   label=_('Send new token'))

    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'email', 'language', 'company',
                  'responsible', 'new_token']

class InitiateHRForm(InitiateCaseForm):
    class Meta:
        model = HR
        fields = ['first_name', 'last_name', 'email', 'language', 'company',
                  'responsible', 'new_token', 'is_admin']

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
    company = forms.CharField(required=False, widget=forms.HiddenInput())

