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
