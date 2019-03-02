from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

User = get_user_model()

class UserCreateForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ['email', 'first_name', 'last_name', 'role', 'billing',
                  'password1', 'password2']

class UserUpdateForm(UserChangeForm):
    password = None
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_active', 'is_staff',
                  'role', 'billing']

class UserPasswordUpdateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['password1', 'password2']

