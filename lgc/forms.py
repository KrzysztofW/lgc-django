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

def datepicker_set_widget_attrs(obj, field, attrs=None, tpl=None):
    if translation.get_language() == 'fr':
        obj.fields[field].widget = DatePickerInput(format='%d/%m/%Y',
                                                   attrs=attrs)
    else:
        obj.fields[field].widget = DatePickerInput(format='%m/%d/%Y',
                                                   attrs=attrs)
    if tpl:
        obj.fields[field].widget.template_name = tpl

class LgcTab(Tab):
    link_template = 'lgc/lgc_tab.html'
    lgc_active = False

    def render_link(self, *args, **kwargs):
        return render_to_string(self.link_template, {'link': self})

    def __init__(self, *args, **kwargs):
        self.lgc_active = kwargs.get("lgc_active", False)
        super().__init__(*args, **kwargs)

SEARCH_PROCESS_STATE = (
    ('', '------'),
    ('A', _('Active')),
    ('I', _('Inactive')),
)

class PersonSearchForm(forms.Form):
    id = forms.CharField(required=False)
    info_process = forms.ChoiceField(required=False,
                                     choices=lgc_models.PROCESS_CHOICES,
                                     label=_('Immigration Process'),
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
    start_date = forms.CharField(required=False, label=_('Start Date'))
    process_state = forms.ChoiceField(required=False, label=_('Process State'),
                                     choices=SEARCH_PROCESS_STATE,
                                     widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        datepicker_set_widget_attrs(self, 'start_date')

class PersonCreateForm(forms.ModelForm):
    is_private = forms.BooleanField(required=False, initial=False,
                                    help_text=_('Designates whether this file is private (not related to a corporation).'))
    active_tab = forms.CharField(required=True, widget=forms.HiddenInput())
    birth_date = forms.DateField(label=_('Birth Date'))
    home_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Home Entity Address'))
    host_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Host Entity Address'))

    responsible = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple(attrs={'class':'form-control'}), queryset=user_models.get_local_user_queryset())
    start_date = forms.DateField(label=_('Start Date'))
    local_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80, 'onchange':'auto_complete_region(this);'}),
                                    label=_('Local Address'))

    foreign_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Foreign Address'))
    comments = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Comments'))
    process_name = forms.ModelChoiceField(required=False,
                                          queryset=lgc_models.Process.objects.all(),
                                          label=_('Create an active process'))
    foreign_country = CountryField().formfield(label=_('Foreign country'),
                                               required=False,
                                               widget=forms.Select(attrs={'onchange':'auto_complete_jurisdiction(this);'}))
    passport_expiry = forms.DateField(required=False,
                                      label=_('Passport Expiry'))
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput(),
                                 initial=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        datepicker_set_widget_attrs(self, 'birth_date')
        datepicker_set_widget_attrs(self, 'spouse_birth_date')
        if self.fields.get('start_date'):
            datepicker_set_widget_attrs(self, 'start_date')

    class Meta:
        model = lgc_models.Person
        exclude = ['creation_date', 'modified_by', 'modification_date']

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
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class':'form-control lgc_small_formset'}))
    birth_date = forms.DateField(label=_('Birth Date'))
    passport_expiry = forms.DateField(required=False, label=_('Passport Expiry'))
    passport_nationality = CountryField().formfield(label=_('Passport nationality'), required=False, widget=forms.Select(attrs={'class':'form-control lgc_small_formset', 'style':'width:90px;'}))
    # DCEM expiration
    dcem_end_date = forms.DateField(required=False, label=_('VLTS-TS/DCEM Expiry'))
    dcem_enabled = forms.BooleanField(required=False, label=_('Enabled'),
                                      initial=True)

    class Meta:
        model = lgc_models.Child
        exclude = ['person', 'expiration']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        datepicker_set_widget_attrs(self, 'birth_date', attrs={'class':'form-control lgc_small_formset'}, tpl='lgc/date-picker.html')
        datepicker_set_widget_attrs(self, 'passport_expiry', attrs={'class':'form-control lgc_small_formset'}, tpl='lgc/date-picker.html')
        if self.fields.get('dcem_end_date'):
            datepicker_set_widget_attrs(self, 'dcem_end_date', attrs={'class':'form-control lgc_small_formset'}, tpl='lgc/date-picker.html')
            self.fields['dcem_enabled'].initial = True

class ExpirationCommon(forms.ModelForm):
    start_date = forms.DateField(label=_('Start Date'))
    end_date = forms.DateField(label=_('End Date'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        datepicker_set_widget_attrs(self, 'start_date', attrs={'class':'form-control lgc_small_formset'}, tpl='lgc/date-picker.html')
        datepicker_set_widget_attrs(self, 'end_date', attrs={'class':'form-control lgc_small_formset'}, tpl='lgc/date-picker.html')

    class Meta:
        abstract = True

class ExpirationForm(ExpirationCommon):
    options = empty_select + lgc_models.PERSON_EXPIRATIONS_CHOICES
    type = forms.ChoiceField(choices=options, widget=forms.Select(attrs={'class':'form-control lgc_small_formset',
                                                                         'style':'width:195px;'}))

    class Meta:
        model = lgc_models.Expiration
        fields = ['type', 'start_date', 'end_date', 'enabled']

class SpouseExpirationForm(ExpirationCommon):
    options = empty_select + lgc_models.PERSON_SPOUSE_EXPIRATIONS_CHOICES_SHORT
    type = forms.ChoiceField(choices=options, widget=forms.Select(attrs={'class':'form-control lgc_small_formset',
                                                                         'style':'width:195px;'}))

    class Meta:
        model = lgc_models.Expiration
        fields = ['type', 'start_date', 'end_date', 'enabled']

class ArchiveBoxForm(forms.ModelForm):
    number = forms.IntegerField(label=_('Number'), min_value=0,
                                widget=forms.NumberInput(attrs={'class':'form-control'}))

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
    id = forms.CharField(required=True, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        datepicker_set_widget_attrs(self, 'validation_date')

    class Meta:
        model = lgc_models.PersonProcessStage
        exclude = ['person_process', 'is_specific']

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
PROCESS_STAGE_COMPLETED = 'C'

PROCESS_STAGE_COMMON_CHOICES = (
    (PROCESS_STAGE_NONE, _('No action')),
    (PROCESS_STAGE_DELETE, _('Delete last stage')),
    (PROCESS_STAGE_ADD_SPECIFIC, _('Add specific stage')),
)
PROCESS_STAGE_CHOICES = PROCESS_STAGE_COMMON_CHOICES + (
    (PROCESS_STAGE_VALIDATE, _('Validate stage')),
)

FINAL_PROCESS_STAGE_CHOICES = PROCESS_STAGE_COMMON_CHOICES + (
    (PROCESS_STAGE_COMPLETED, _('Completed')),
)

class UnboundPersonProcessStageForm(forms.Form):
    action = forms.ChoiceField(label=_('Action:'),
                               required=False, choices=PROCESS_STAGE_CHOICES,
                               widget = forms.RadioSelect(attrs = {
                                   'onclick' : "specific_stage_action(this);",
                               }))
    class Meta:
        fields = '__all__'

class UnboundFinalPersonProcessStageForm(UnboundPersonProcessStageForm):
    action = forms.ChoiceField(label=_('Action:'),
                               required=False, choices=FINAL_PROCESS_STAGE_CHOICES,
                               widget = forms.RadioSelect(attrs = {
                                   'onclick' : "specific_stage_action(this);",
                               }))
    class Meta:
        fields = '__all__'

class PersonProcessForm(forms.ModelForm):
    class Meta:
        model = lgc_models.PersonProcess
        exclude = ['name_en', 'name_fr']

class PersonProcessCompleteForm(forms.ModelForm):
    name_fr = forms.CharField(required=False, label=_('French name'))
    name_en = forms.CharField(required=False, label=_('English name'))

    class Meta:
        model = lgc_models.PersonProcess
        exclude = ['person', 'process', 'active', 'name_en', 'name_fr']

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
                                    lgc_models.EXPIRATION_CHOICES + lgc_models.EXPIRATION_CHOICES_DCEM,
                                    widget=forms.Select(attrs={'class':'form-control',
                                                               'onchange':'form.submit();'}))

    expires = forms.IntegerField(required=False, label=_('Expires in days'),
                                 min_value=0, max_value=10000,
                                 widget=forms.NumberInput(attrs={'onchange':'form.submit();'}))
    show_disabled = forms.BooleanField(required=False, label=_('Show disabled'),
                                       widget=forms.CheckboxInput(attrs={'onchange':'form.submit();'}))

    class Meta:
        fields = '__all__'

CHANGES_DETECTED_FORCE = 'F'
CHANGES_DETECTED_DISCARD = 'D'
CHANGES_DETECTED_CHOICES = (
    (CHANGES_DETECTED_FORCE, _('Apply my changes anyway.')),
    (CHANGES_DETECTED_DISCARD, _('Discard all my changes and redisplay.')),
)

class ChangesDetectedForm(forms.Form):
    changes_action = forms.ChoiceField(required=False, choices=CHANGES_DETECTED_CHOICES,
                                       widget=forms.RadioSelect(),
                                       label=_('Choose an action:'))
    class Meta:
        fields = '__all__'

class InvoiceCreateForm(forms.ModelForm):
    invoice_date = forms.DateField(label=_('Invoice Date'))
    modification_date = forms.DateField(required=False, label=_('Modification Date'))
    po_date = forms.DateField(required=False, label=_('Date'))
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput(),
                                 initial=0)
    client = forms.ModelChoiceField(queryset=lgc_models.Client.objects,
                                    widget=forms.HiddenInput())
    client_update = forms.BooleanField(required=False, widget=forms.HiddenInput(),
                                       initial=False)
    various_expenses = forms.BooleanField(label=_('Include Various Expenses'),
                                          required=False, initial=False,
                                          help_text="(Phone, mail...) 5% of the services limited to 100.",
                                          widget=forms.CheckboxInput(attrs={'onchange':'return compute_invoice();'}))
    total = forms.FloatField(min_value=0, widget=forms.HiddenInput(), initial=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        datepicker_set_widget_attrs(self, 'invoice_date')
        datepicker_set_widget_attrs(self, 'modification_date')
        datepicker_set_widget_attrs(self, 'po_date')
        self.fields['with_regard_to'].widget.attrs['disabled'] = True

    class Meta:
        model = lgc_models.Invoice
        exclude = ['modified_by', 'person', 'process', 'type', 'id', 'number',
                   'state', 'already_paid']

INVOICE_SEARCH_DATE_INVOICE = 'I'
INVOICE_SEARCH_DATE_PAY = 'P'
INVOICE_SEARCH_DATE_CHOICES = (
    (INVOICE_SEARCH_DATE_INVOICE, _('Validation Date')),
    (INVOICE_SEARCH_DATE_PAY, _('Payment Date')),
)

class InvoiceSearchForm(forms.Form):
    number = forms.CharField(required=False, label='ID')
    dates = forms.ChoiceField(label='&nbsp;', required=False,
                              choices=INVOICE_SEARCH_DATE_CHOICES,
                              widget = forms.RadioSelect(attrs = {
                                  'onchange':'form.submit();',
                              }),
                              initial=INVOICE_SEARCH_DATE_INVOICE)
    start_date = forms.CharField(required=False, label=_('Start Date'))
    end_date = forms.CharField(required=False, label=_('End Date'))
    state = forms.ChoiceField(required=False,
                              choices=(('', '---------'),) + lgc_models.INVOICE_STATE_CHOICES,
                              label=_('State'),
                              widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}))
    responsible = forms.ModelChoiceField(required=False, label=_('Responsible'),
                                         widget=forms.Select(attrs={'class':'form-control', 'onchange':'form.submit();'}),
                                         queryset=user_models.get_local_user_queryset())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        datepicker_set_widget_attrs(self, 'start_date')
        datepicker_set_widget_attrs(self, 'end_date')

class InvoiceUpdateForm(InvoiceCreateForm):
    number = forms.IntegerField(min_value=1, widget=forms.HiddenInput())
    already_paid = forms.FloatField(required=False, min_value=0, widget=forms.NumberInput(attrs={'class':'form-control lgc_pull-right', 'onchange':'return compute_invoice();', 'step': "0.01"}), initial=0)
    class Meta:
        model = lgc_models.Invoice
        exclude = ['modified_by', 'person', 'process', 'type', 'id', 'total']

class ClientCreateForm(forms.ModelForm):
    address = forms.CharField(required=False,
                              widget=forms.Textarea(attrs={'rows': 3, 'cols': 33}))

    class Meta:
        model = lgc_models.Client
        exclude = ['id']

class InvoiceCommonForm(forms.ModelForm):
    quantity = forms.IntegerField(required=False, min_value=0, widget=forms.NumberInput(attrs={'style':'height:30px;', 'class':'form-control lgc_pull-right', 'onchange':'return compute_invoice();'}), initial=1)
    vat = forms.ChoiceField(required=False, choices=lgc_models.VAT_CHOICES,
                            widget=forms.Select(attrs={'style':'height:30px; width:60px;',
                                                       'class':'form-control lgc_pull-right',
                                                       'onchange':'return compute_invoice();'}))
    rate = forms.FloatField(required=False, min_value=0, widget=forms.NumberInput(attrs={'style':'height:30px;', 'class':'form-control lgc_pull-right', 'onchange':'return compute_invoice();', 'step': "0.01"}), initial=0)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1,
                                                                               'class':'form-control'}))
    total = forms.FloatField(required=False, min_value=0, widget=forms.TextInput(attrs={'style':'height:30px;', 'class':'form-control lgc_pull-right', 'readonly':'yes', 'step': "0.01"}), initial=0)

    class Meta:
        abstract = True

class InvoiceItemForm(InvoiceCommonForm):
    item_id = forms.CharField(label='ID', required=False, widget=forms.TextInput(attrs={'style':'height:30px;', 'class':'form-control', 'readonly':'yes'}))

    class Meta:
        model = lgc_models.InvoiceItem
        exclude = ['invoice']

class ItemForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3,
                                                               'class':'form-control'}))

    class Meta:
        model = lgc_models.Item
        exclude = ['invoice']

class InvoiceDisbursementForm(InvoiceCommonForm):
    disbursement_id = forms.CharField(label='ID', required=False, widget=forms.TextInput(attrs={'style':'height:30px;', 'class':'form-control', 'readonly':'yes'}))
    margin = forms.BooleanField(label=_('20% margin'), required=False, initial=False,
                                widget=forms.CheckboxInput(attrs={'class':'lgc_aligned_checkbox', 'onchange':'return compute_invoice();'}))

    class Meta:
        model = lgc_models.InvoiceDisbursement
        exclude = ['invoice']

class DisbursementForm(ItemForm):
    class Meta:
        model = lgc_models.Disbursement
        exclude = ['invoice']

class DisbursementDocumentForm(DocumentForm):
    class Meta:
        model = lgc_models.DisbursementDocument
        fields = ['document', 'description']

class DisbursementDocumentFormSet(DocumentFormSet):
    id = forms.CharField(required=True, widget=forms.HiddenInput())

    class Meta:
        model = lgc_models.DisbursementDocument
        fields = ['id']

class SettingsForm(forms.ModelForm):
    class Meta:
        model = lgc_models.Settings
        fields = '__all__'
