from django.utils import translation
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

empty_select = (('', '----'),)

def datepicker_set_lang_widget(obj, field):
    if translation.get_language() == 'fr':
        obj.fields[field].widget = DatePickerInput(format='%d/%m/%Y')
    else:
        obj.fields[field].widget = DatePickerInput(format='%m/%d/%Y')

class LgcTab(Tab):
    link_template = 'lgc/lgc_tab.html'
    lgc_active = False

    def render_link(self, *args, **kwargs):
        return render_to_string(self.link_template, {'link': self})

    def __init__(self, *args, **kwargs):
        self.lgc_active = kwargs.get("lgc_active", False)
        super().__init__(*args, **kwargs)

class PersonSearchForm(forms.Form):
    id = forms.CharField(required=False, )
    info_process = forms.ChoiceField(required=False,
                                     choices=lgc_models.PROCESS_CHOICES,
                                     label=_('Process'),
                                     widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}))
    state = forms.ChoiceField(required=False,
                              choices=lgc_models.FILE_STATE_CHOICES,
                              label=_('State'),
                              widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}))
    jurist = forms.ModelChoiceField(required=False, label=_('Jurist'),
                                    widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}),
                                    queryset=user_models.get_jurist_queryset())
    consultant = forms.ModelChoiceField(required=False, label=_('Consultant'),
                                        widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}),
                                        queryset=user_models.get_consultant_queryset())
    prefecture = forms.ChoiceField(required=False, label=_('Prefecture'),
                                   choices=lgc_models.PREFECTURE_CHOICES,
                                   widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}))
    subprefecture = forms.ChoiceField(required=False, label=_('Subprefecture'),
                                      choices=lgc_models.SUBPREFECTURE_CHOICES,
                                      widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}))
    consulate = forms.ChoiceField(required=False, label=_('Consulate'),
                                  choices=lgc_models.CONSULATE_CHOICES,
                                  widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}))
    direccte = forms.ChoiceField(required=False, label='DIRECCTE',
                                 choices=lgc_models.DIRECCTE_CHOICES,
                                 widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}))
    jurisdiction = forms.ChoiceField(required=False, label=_('Jurisdiction'),
                                     choices=lgc_models.JURISDICTION_SPECIFIQUE_CHOICES,
                                     widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}))
    start_date = forms.CharField(required=False,
                                 widget=DatePickerInput(attrs={'onchange':'form.submit();'}),
                                 label=_('Start Date'))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        datepicker_set_lang_widget(self, 'start_date')

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
    passport_expiry = forms.DateField(required=False,
                                      widget=DatePickerInput(),
                                      label=_('Passport Expiry'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        datepicker_set_lang_widget(self, 'birth_date')
        datepicker_set_lang_widget(self, 'start_date')

    class Meta:
        model = lgc_models.Person
        exclude = ['creation_date', 'modified_by']

class InitiateAccountForm(forms.ModelForm):
    responsible = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple(attrs={'class':'form-control'}), queryset=user_models.get_local_user_queryset(), label=_('Persons in charge'))
    new_token = forms.BooleanField(required=False, initial=True,
                                   label=_('Send new token'),
                                   help_text=_('Send authentication token allowing to choose a new password.'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        if self.fields.get('status', ''):
            self.fields['status'].required = False

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'language',
                  'responsible', 'new_token', 'is_active', 'status']

class InitiateHRForm(InitiateAccountForm):
    active_tab = forms.CharField(required=True, widget=forms.HiddenInput())
    is_admin = forms.BooleanField(required=False, label=_('Is admin'),
                                  help_text=_('This HR user can initiate new cases'))

    class Meta:
        model = User
        fields = ['active_tab', 'first_name', 'last_name', 'email', 'language',
                  'company', 'responsible', 'new_token', 'is_admin',
                  'is_active', 'status']

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        datepicker_set_lang_widget(self, 'birth_date')
        datepicker_set_lang_widget(self, 'passport_expiry')

class ExpirationCommon(forms.ModelForm):
    start_date = forms.DateField(widget=DatePickerInput(), label=_('Start Date'))
    end_date = forms.DateField(widget=DatePickerInput(), label=_('End Date'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        datepicker_set_lang_widget(self, 'start_date')
        datepicker_set_lang_widget(self, 'end_date')

    class Meta:
        abstract = True

class ExpirationForm(ExpirationCommon):
    options = empty_select + lgc_models.PERSON_EXPIRATIONS_CHOICES
    type = forms.ChoiceField(choices=options)

    class Meta:
        model = lgc_models.Expiration
        fields = ['type', 'start_date', 'end_date', 'enabled']

class SpouseExpirationForm(ExpirationCommon):
    options = empty_select + lgc_models.PERSON_SPOUSE_EXPIRATIONS_CHOICES_SHORT
    type = forms.ChoiceField(choices=options)

    class Meta:
        model = lgc_models.Expiration
        fields = ['type', 'start_date', 'end_date', 'enabled']

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

class ExpirationSearchForm(forms.Form):
    user = forms.ModelChoiceField(required=False, label=_('Responsible'),
                                  widget=forms.Select(attrs={'class':'form-control',
                                                             'onchange':'form.submit();'}),
                                  queryset=user_models.get_local_user_queryset())
    expiry_type = forms.ChoiceField(label=_('Expiration Type'),
                                    required=False,
                                    choices=empty_select +
                                    lgc_models.EXPIRATION_CHOICES,
                                    widget=forms.Select(attrs={'class':'form-control',
                                                               'onchange':'form.submit();'}))

    expires = forms.IntegerField(required=False, label=_('Expires in days'),
                                 min_value=0, max_value=10000,
                                 widget=forms.NumberInput(attrs={'onchange':'form.submit();'}))
    show_disabled = forms.BooleanField(required=False, label=_('Show disabled'),
                                       widget=forms.CheckboxInput(attrs={'onchange':'form.submit();'}))

    class Meta:
        fields = '__all__'
