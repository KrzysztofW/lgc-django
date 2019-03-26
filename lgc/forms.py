from django import forms
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from . import models as lgc_models
from users import models as user_models
from django.contrib.auth import get_user_model
User = get_user_model()

class PersonCreateForm(forms.ModelForm):
    birth_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date', 'class':'form-control', 'style':'width:155px'}), label=_('Birth Date'))
    home_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Home Entity Address'))
    host_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Host Entity Address'))

    responsible = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple(attrs={'class':'form-control'}), queryset=user_models.get_local_user_queryset())
    start_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date', 'class':'form-control', 'style':'width:155px'}))
    local_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Local Address'))
    foreign_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Foreign Address'))
    comments = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Comments'))
    process_name = forms.ModelChoiceField(required=False,
                                          queryset=lgc_models.Process.objects.all(),
                                          label=_('Create an active process'))

    class Meta:
        model = lgc_models.Person
        exclude = ['creation_date', 'modified_by']

class InitiateAccountForm(forms.ModelForm):
    responsible = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple(attrs={'class':'form-control'}), queryset=user_models.get_local_user_queryset(), label=_('Persons in charge'))
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

class HREmployeeForm(forms.Form):
    id = forms.CharField(required=True, widget=forms.HiddenInput())
    first_name = forms.CharField(required=True, widget=forms.HiddenInput())
    last_name = forms.CharField(required=True, widget=forms.HiddenInput())
    email = forms.EmailField(required=True, widget=forms.HiddenInput())

class ProcessForm(forms.Form):
    name = forms.ModelChoiceField(queryset=lgc_models.PersonProcess.objects.all())

# children:
class ChildCreateForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    birth_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date', 'class':'form-control', 'style':'width:155px'}), label=_('Birth Date'))
    passport_expiry = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date', 'class':'form-control', 'style':'width:155px'}), label=_('Passport Expiry'))
    passport_nationality = CountryField().formfield(required=False, widget=forms.Select(attrs={'class':'form-control', 'style': 'width:100px'}))

    class Meta:
        model = lgc_models.Child
        exclude = ['person']

class ModerationChildCreateForm(ChildCreateForm):
    class Meta:
        model = lgc_models.ModerationChild
        exclude = ['person']

class AuthorizationsCommonForm(forms.ModelForm):
    start_date = forms.DateField(required=True, widget=forms.TextInput(attrs={'type': 'date', 'class':'form-control', 'style':'width:155px'}), label=_('Start Date'))
    end_date = forms.DateField(required=True, widget=forms.TextInput(attrs={'type': 'date', 'class':'form-control', 'style':'width:155px'}), label=_('End Date'))

    class Meta:
        abstract = True

# Visa:
class VisaResidencePermitForm(AuthorizationsCommonForm):
    class Meta:
        model = lgc_models.VisaResidencePermit
        fields = ['type', 'start_date', 'end_date', 'enabled']

class ModerationVisaResidencePermitForm(AuthorizationsCommonForm):
    class Meta:
        model = lgc_models.ModerationVisaResidencePermit
        fields = ['type', 'start_date', 'end_date', 'enabled']

class SpouseVisaResidencePermitForm(AuthorizationsCommonForm):
    class Meta:
        model = lgc_models.SpouseVisaResidencePermit
        fields = ['type', 'start_date', 'end_date', 'enabled']

class ModerationSpouseVisaResidencePermitForm(AuthorizationsCommonForm):
    class Meta:
        model = lgc_models.ModerationSpouseVisaResidencePermit
        fields = ['type', 'start_date', 'end_date', 'enabled']

# Work Permit:
class WorkPermitForm(AuthorizationsCommonForm):
    class Meta:
        model = lgc_models.WorkPermit
        fields = ['start_date', 'end_date', 'enabled']

class ModerationWorkPermitForm(AuthorizationsCommonForm):
    class Meta:
        model = lgc_models.ModerationWorkPermit
        fields = ['start_date', 'end_date', 'enabled']

class SpouseWorkPermitForm(AuthorizationsCommonForm):
    class Meta:
        model = lgc_models.SpouseWorkPermit
        fields = ['start_date', 'end_date', 'enabled']

class ModerationSpouseWorkPermitForm(AuthorizationsCommonForm):
    class Meta:
        model = lgc_models.ModerationSpouseWorkPermit
        fields = ['start_date', 'end_date', 'enabled']

class ArchiveBoxForm(forms.ModelForm):
    class Meta:
        model = lgc_models.ArchiveBox
        fields = ['number']

class ProcessForm(forms.ModelForm):
    stages = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple(attrs={'class':'form-control', 'size': 15}), queryset = lgc_models.ProcessStage.objects.all())
    class Meta:
        model = lgc_models.Process
        fields = '__all__'

class ProcessStageForm(forms.ModelForm):
    class Meta:
        model = lgc_models.ProcessStage
        fields = '__all__'

class PersonProcessStageForm(forms.ModelForm):
    stage_comments = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))

    class Meta:
        model = lgc_models.PersonProcessStage
        fields = '__all__'

class UnboundPersonProcessStageForm(forms.Form):
    stage_comments = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'cols': 33}))
    validate_stage = forms.BooleanField(required=False, initial=False,
                                        label=_('Validate Stage'),
                                        help_text=_('Validate this stage and set the next one.'))
    delete = forms.BooleanField(required=False, initial=False, label=_('Delete last stage'))
    name_fr = forms.CharField(required=False)
    name_en = forms.CharField(required=False)

    class Meta:
        fields = '__all__'
