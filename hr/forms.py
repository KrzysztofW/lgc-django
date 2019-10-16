from django.utils import translation
from django import forms
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from crispy_forms.bootstrap import Tab
from django.template.loader import render_to_string
from bootstrap_datepicker_plus import DatePickerInput
from lgc import models as lgc_models
from lgc import forms as lgc_forms
from users import models as user_models
from django.contrib.auth import get_user_model
from django_countries.fields import CountryField

User = get_user_model()

empty_select = (('', '----'),)

class HRCreateEmployeeAccountForm(lgc_forms.CreateAccountForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsible'].required = False

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'language']

class EmployeeSearchForm(forms.Form):
    home_entity = forms.CharField(required=False, label=_('Home Entity'))
    host_entity = forms.CharField(required=False, label=_('Host Entity'))
    first_name = forms.CharField(required=False, label=_('First Name'))
    last_name = forms.CharField(required=False, label=_('Last Name'))

class ExpirationSearchForm(forms.Form):
    first_name = forms.CharField(required=False, label=_('First Name'))
    last_name = forms.CharField(required=False, label=_('Last Name'))
    expires = forms.IntegerField(required=False, label=_('Expires in days'),
                                 min_value=0, max_value=10000,
                                 widget=forms.NumberInput(attrs={'onchange':'form.submit();'}))
    show_disabled = forms.BooleanField(required=False, label=_('Show disabled'),
                                       widget=forms.CheckboxInput(attrs={'onchange':'form.submit();'}))
    show_expired = forms.BooleanField(required=False, label=_("Show expired"),
                                      widget=forms.CheckboxInput(attrs={'onchange':'form.submit();'}))

    class Meta:
        fields = '__all__'

class InitiateCaseForm(forms.Form):
    first_name = forms.CharField(label=_('Given Name of the employee (as per passport)'))
    last_name = forms.CharField(label=_('Surname of the employee (as per passport)'))
    citizenship = CountryField().formfield(label=_('Citizenship'))
    address = forms.CharField(label=_('Work location in France (company name and detailed address)'),
                              widget=forms.Textarea(attrs={'rows': 3, 'cols': 80}))
    start_date = forms.CharField(required=False, label=_('Intended start date'))
    expected_assignment = forms.CharField(required=False, label=_('Expected assignment or contract duration'))

    hr_contact = forms.CharField(label=_('HR contact for the case'))
    dependents = forms.BooleanField(required=False, initial=False,
                                    label=_('Dependents yes/no'))
    email = forms.EmailField(label=_("Assignee's email address"))
    assistance_type = forms.CharField(label=_('Type of assistance required'))
    comments = forms.CharField(label=_('Comments and additional information on the case'),
                               help_text=_('For non applicable information please indicate "NA"'),
                               widget=forms.Textarea(attrs={'rows': 3, 'cols': 80}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lgc_forms.datepicker_set_widget_attrs(self, 'start_date')
