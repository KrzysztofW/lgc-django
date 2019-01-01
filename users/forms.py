from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']

class UserPasswordUpdateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['password1', 'password2']

class ProfileCreateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['role', 'billing']
