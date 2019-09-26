from django import forms
from django.utils.translation import ugettext_lazy as _
from bootstrap_datepicker_plus import DatePickerInput
from lgc import forms as lgc_forms
from lgc import models as lgc_models
from . import models as employee_models

class EmployeeUpdateForm(forms.ModelForm):
    first_name = forms.CharField(required=False, label=_('First Name'),
                                 help_text=_('As per passport'))
    last_name = forms.CharField(required=False, label=_('Last Name'),
                                 help_text=_('As per passport'))

    active_tab = forms.CharField(required=True, widget=forms.HiddenInput())
    birth_date = forms.DateField(widget=DatePickerInput(), label=_('Birth Date'))
    home_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'cols': 80}), label=_('Home Entity Address'))
    host_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'cols': 80}), label=_('Host Entity Address'))

    local_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'cols': 80}), label=_('Home Address in France'))
    foreign_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'cols': 80}), label=_('Home Address outside France'))
    passport_expiry = forms.DateField(required=False,
                                      widget=DatePickerInput(),
                                      label=_('Passport Expiry'))
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput())

    class Meta:
        model = employee_models.Employee
        exclude = ['modified_by', 'modification_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lgc_forms.datepicker_set_widget_attrs(self, 'birth_date')
        lgc_forms.datepicker_set_widget_attrs(self, 'spouse_birth_date')
        lgc_forms.datepicker_set_widget_attrs(self, 'passport_expiry')
        lgc_forms.datepicker_set_widget_attrs(self, 'spouse_passport_expiry')

class ChildCreateForm(lgc_forms.ChildCreateForm):
    # unset DCEM/TIR expiration
    dcem_id = None
    dcem_end_date = None
    dcem_enabled = None

    class Meta:
        model = employee_models.Child
        exclude = ['person', 'expiration', 'dcem_id',
                   'dcem_end_date', 'dcem_enabled', 'person_child']

class ChildCreateForm2(lgc_forms.ChildCreateForm):
    class Meta:
        model = employee_models.Child
        exclude = ['person', 'expiration', 'person_child']

class ModerationPersonCreateForm(lgc_forms.PersonCreateForm):
    active_tab = None
    responsible = None
    comments = None
    process_name = None
    start_date = None
    is_private = None

    class Meta:
        model = lgc_models.Person
        exclude = ['modified_by', 'modification_date', 'creation_date', 'id', 'user',
                   'prefecture', 'subprefecture', 'consulate', 'direccte',
                   'info_process', 'responsible', 'start_date', 'state', 'comments',
                   'is_private', 'work_permit']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.fields.keys():
            if key == 'version':
                continue
            self.fields[key].widget.attrs['disabled'] = True

class ModerationEmployeeUpdateForm(EmployeeUpdateForm):
    active_tab = None

    class Meta:
        model = employee_models.Employee
        exclude = ['modified_by', 'updated', 'user', 'is_private']

class DocumentFormSet(forms.ModelForm):
    id = forms.CharField(required=True, widget=forms.HiddenInput())
    reject = forms.BooleanField(required=False, label=_('Reject change'))
    description = forms.CharField(required=False, label=_('Description'))

    class Meta:
        model = lgc_models.Document
        fields = ['id', 'description', 'added', 'deleted', 'reject' ]
