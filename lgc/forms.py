from django import forms
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from crispy_forms.bootstrap import Tab
from django.template.loader import render_to_string
from bootstrap_datepicker_plus import DatePickerInput
from . import models as lgc_models
from users import models as user_models
from django.contrib.auth import get_user_model
from django_countries.fields import CountryField

User = get_user_model()

class LgcTab(Tab):
    link_template = 'lgc/lgc_tab.html'
    lgc_active = False

    def render_link(self, *args, **kwargs):
        return render_to_string(self.link_template, {'link': self})

    def __init__(self, *args, **kwargs):
        self.lgc_active = kwargs.get("lgc_active", False)
        super().__init__(*args, **kwargs)

class EmployeeUpdateForm(forms.ModelForm):
    active_tab = forms.CharField(required=True, widget=forms.HiddenInput())
    birth_date = forms.DateField(widget=DatePickerInput(), label=_('Birth Date'))
    home_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Home Entity Address'))
    host_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Host Entity Address'))

    local_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Local Address'))
    foreign_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Foreign Address'))
    comments = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Comments'))

    class Meta:
        model = lgc_models.Person
        exclude = ['creation_date', 'modified_by', 'responsible',
                   'info_process', 'state']

class PersonCreateForm(forms.ModelForm):
    active_tab = forms.CharField(required=True, widget=forms.HiddenInput())
    birth_date = forms.DateField(widget=DatePickerInput(), label=_('Birth Date'))
    home_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Home Entity Address'))
    host_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Host Entity Address'))

    responsible = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple(attrs={'class':'form-control'}), queryset=user_models.get_local_user_queryset())
    start_date = forms.DateField(widget=DatePickerInput(), label=_('Start Date'))
    local_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80, 'onchange':'auto_complete_region(this);'}),
                                    label=_('Local Address'))

    foreign_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Foreign Address'))
    comments = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Comments'))
    process_name = forms.ModelChoiceField(required=False,
                                          queryset=lgc_models.Process.objects.all(),
                                          label=_('Create an active process'))
    foreign_country = CountryField().formfield(required=False,
                                               widget=forms.Select(attrs={'onchange':'auto_complete_jurisdiction(this);'}))

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
    active_tab = forms.CharField(required=True, widget=forms.HiddenInput())
    is_admin = forms.BooleanField(required=False, label=_('Is admin'),
                                  help_text=_('This HR user can initiate new cases'))

    class Meta:
        model = User
        fields = ['active_tab', 'first_name', 'last_name', 'email', 'language',
                  'company', 'responsible', 'new_token', 'is_admin', 'is_active']

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
    birth_date = forms.DateField(widget=DatePickerInput(), label=_('Birth Date'))
    passport_expiry = forms.DateField(widget=DatePickerInput(), label=_('Passport Expiry'))
    passport_nationality = CountryField().formfield(required=False, widget=forms.Select(attrs={'class':'form-control', 'style': 'width:150px'}))

    class Meta:
        model = lgc_models.Child
        exclude = ['person']

class ModerationChildCreateForm(ChildCreateForm):
    class Meta:
        model = lgc_models.ModerationChild
        exclude = ['person']

class AuthorizationsCommonForm(forms.ModelForm):
    start_date = forms.DateField(widget=DatePickerInput(), label=_('Start Date'))
    end_date = forms.DateField(widget=DatePickerInput(), label=_('End Date'))

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
        exclude = ['is_specific']

class PersonProcessSpecificStageForm(forms.Form):
    name_fr = forms.CharField(required=False,
                              label=_('Specific stage French name'))
    name_en = forms.CharField(required=False,
                              label=_('Specific stage English name'))

    class Meta:
        fields = '__all__'


PROCESS_STAGE_NONE = '-'
PROCESS_STAGE_DELETE = 'D'
PROCESS_STAGE_ADD_SPECIFIC = 'S'
PROCESS_STAGE_VALIDATE = 'V'
PROCESS_STAGE_GEN_INVOICE_AND_ARCHIVE = 'IA'
PROCESS_STAGE_ARCHIVE = 'A'

PROCESS_STAGE_COMMON_CHOICES = (
    (PROCESS_STAGE_NONE, _('No action')),
    (PROCESS_STAGE_DELETE, _('Delete last stage')),
    (PROCESS_STAGE_ADD_SPECIFIC, _('Add specific stage')),
)
PROCESS_STAGE_CHOICES = PROCESS_STAGE_COMMON_CHOICES + (
    (PROCESS_STAGE_VALIDATE, _('Validate stage')),
)

FINAL_PROCESS_STAGE_CHOICES = PROCESS_STAGE_COMMON_CHOICES + (
    (PROCESS_STAGE_GEN_INVOICE_AND_ARCHIVE,
     _('Generate invoice and archive')),
    (PROCESS_STAGE_ARCHIVE, _('Archive (no invoice)')),
)

class UnboundPersonProcessStageForm(forms.Form):
    stage_comments = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'cols': 33}))
    action = forms.ChoiceField(required=False, choices=PROCESS_STAGE_CHOICES,
                               widget = forms.RadioSelect(attrs = {
                                   'onclick' : "specific_stage_action(this);",
                               }))
    class Meta:
        fields = '__all__'

class UnboundFinalPersonProcessStageForm(UnboundPersonProcessStageForm):
    action = forms.ChoiceField(required=False, choices=FINAL_PROCESS_STAGE_CHOICES,
                               widget = forms.RadioSelect(attrs = {
                                   'onclick' : "specific_stage_action(this);",
                               }))
    class Meta:
        fields = '__all__'

class ConsulatePrefectureForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['consulate'].widget.attrs['disabled'] = True
        self.fields['prefecture'].widget.attrs['disabled'] = True

    class Meta:
        model = lgc_models.PersonProcess
        fields = ['consulate', 'prefecture']

class DocumentForm(forms.ModelForm):
    document = forms.FileField(required=False, label=_('File*'))
    description = forms.CharField(required=False, label=_('Description*'))

    class Meta:
        model = lgc_models.Document
        fields = ['document', 'description']

class DocumentFormSet(forms.ModelForm):
    id = forms.CharField(required=True, widget=forms.HiddenInput())

    class Meta:
        model = lgc_models.Document
        fields = ['id']
