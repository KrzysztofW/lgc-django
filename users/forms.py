from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from users import models as user_models

User = get_user_model()

class UserCreateForm(UserCreationForm):
    role = forms.ChoiceField(choices = user_models.INTERNAL_ROLE_CHOICES)
    class Meta(UserCreationForm):
        model = User
        fields = ['email', 'first_name', 'last_name', 'role', 'billing',
                  'language', 'password1', 'password2']

class UserUpdateForm(UserChangeForm):
    role = forms.ChoiceField(choices = user_models.INTERNAL_ROLE_CHOICES)
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

