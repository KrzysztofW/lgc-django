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

class HRInitiateEmployeeAccountForm(lgc_forms.InitiateAccountForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsible'].required = False

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'language',
                  'new_token', 'is_active']
