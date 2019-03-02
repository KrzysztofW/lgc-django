from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .forms import UserCreateForm, UserUpdateForm
User = get_user_model()

class CustomUserAdmin(UserAdmin):
    add_form = UserCreateForm
    form = UserUpdateForm
    model = User
    list_display = ['email']

admin.site.register(User, UserAdmin)
