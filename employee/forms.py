from django import forms
from django.utils.translation import ugettext_lazy as _
from bootstrap_datepicker_plus import DatePickerInput
from lgc import forms as lgc_forms
from lgc import models as lgc_models
from . import models as employee_models

class EmployeeUpdateForm(forms.ModelForm):
    active_tab = forms.CharField(required=True, widget=forms.HiddenInput())
    birth_date = forms.DateField(widget=DatePickerInput(), label=_('Birth Date'))
    home_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Home Entity Address'))
    host_entity_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Host Entity Address'))

    local_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Local Address'))
    foreign_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}), label=_('Foreign Address'))
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

class ExpirationForm(lgc_forms.ExpirationForm):
    class Meta:
        model = employee_models.Expiration
        fields = ['type', 'start_date', 'end_date', 'enabled']

class SpouseExpirationForm(lgc_forms.SpouseExpirationForm):
    class Meta:
        model = employee_models.Expiration
        fields = ['type', 'start_date', 'end_date', 'enabled']

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
                   'prefecture', 'subprefecture', 'consulate', 'direccte', 'jurisdiction',
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
