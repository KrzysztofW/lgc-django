from django import forms
from django.utils.translation import ugettext_lazy as _
from bootstrap_datepicker_plus import DatePickerInput
from lgc import forms as lgc_forms
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

    class Meta:
        model = employee_models.Employee
        exclude = ['updated']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lgc_forms.datepicker_set_lang_widget(self, 'birth_date')

class ChildCreateForm(lgc_forms.ChildCreateForm):
    class Meta:
        model = employee_models.Child
        exclude = ['person']

class ExpirationForm(lgc_forms.ExpirationForm):
    class Meta:
        model = employee_models.Expiration
        fields = ['type', 'start_date', 'end_date', 'enabled']

class SpouseExpirationForm(lgc_forms.SpouseExpirationForm):
    class Meta:
        model = employee_models.Expiration
        fields = ['type', 'start_date', 'end_date', 'enabled']
