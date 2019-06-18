from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from users import models as user_models
from django.utils.translation import ugettext as _
User = get_user_model()

class UserCreateForm(UserCreationForm):
    role = forms.ChoiceField(choices=user_models.INTERNAL_ROLE_CHOICES, required=False)
    class Meta(UserCreationForm):
        model = User
        fields = ['email', 'first_name', 'last_name', 'role', 'billing',
                  'language', 'password1', 'password2']

class UserUpdateForm(UserChangeForm):
    role = forms.ChoiceField(choices=user_models.INTERNAL_ROLE_CHOICES, required=False)
    password = None
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_active', 'is_staff',
                  'role', 'billing', 'language']

class UserUpdateProfileForm(UserChangeForm):
    password = None
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'language']

class UserPasswordUpdateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['password1', 'password2']

class UserForcePasswordUpdateForm(UserPasswordUpdateForm):
    current_password = forms.CharField(required=False, label=_('Current password'),
                                       min_length=6, widget=forms.PasswordInput())
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = _('New password')
    class Meta:
        model = User
        fields = ['current_password', 'password1', 'password2']

