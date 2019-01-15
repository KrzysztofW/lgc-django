from common.utils import pagination
from django.http import Http404
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout_then_login
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from functools import wraps
from .models import Profile
from .forms import UserCreateForm, UserUpdateForm, ProfileCreateForm, UserPasswordUpdateForm
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  DeleteView)

def must_be_staff(view_func):
    @wraps(view_func)
    def func_wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return func_wrapper

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'users/list.html'
    context_object_name = 'users'

    def test_func(self):
        return self.request.user.is_staff

    def get_ordering(self):
        return self.request.GET.get('order_by', '-date_joined')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_queryset(self):
        term = self.request.GET.get('term', '')
        order_by = self.request.GET.get('order_by', '-date_joined')
        return User.objects.filter(username__istartswith=term).order_by(order_by)|User.objects.filter(email__istartswith=term)|User.objects.filter(first_name__istartswith=term)|User.objects.filter(last_name__istartswith=term)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_by = self.request.GET.get('order_by', '-date_joined')
        context['title'] = _("Users")
        return pagination(self, context, reverse_lazy('lgc-users'))

        def test_func(self):
            return self.request.user.is_staff

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'users/confirm_delete.html'
    success_url = reverse_lazy('lgc-users')
    success_message = _("User deleted successfully.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Delete User")
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

@login_required
@must_be_staff
def create(request):
    title = _("New User")

    if request.method == 'POST':
        u_form = UserCreateForm(request.POST)
        p_form = ProfileCreateForm(request.POST)

        if u_form.is_valid() and p_form.is_valid():
            user = u_form.save()
            profile = p_form.save(commit=False)
            profile.user = user
            profile.save()
            username = u_form.cleaned_data.get('username')
            messages.success(request,
                             _('The account for %(username)s has been created') %
                             { 'username': username})
            return redirect('lgc-user-create')
        context = {
            'u_form': u_form,
            'p_form': p_form,
            'title': title,
        }
        return render(request, 'users/create.html', context)

    context = {
        'u_form': UserCreateForm(),
        'p_form': ProfileCreateForm(),
        'title': title,
    }
    return render(request, 'users/create.html', context)

@login_required
@must_be_staff
def password_reset(request, user_id):
    user = User.objects.filter(id=user_id)
    title = _("Password Reset")

    if user.count() != 1:
        raise Http404
    if request.method == 'POST':
        form = UserPasswordUpdateForm(request.POST, instance=user[0])
        if form.is_valid():
            form.save()
            messages.success(request,
                             _('The password for %(username)s has been successfully updated') %
                             { 'username': user[0].username})
            return redirect('lgc-user', user[0].id)
        context = {
            'form': form,
            'user': user[0],
            'title': title,
        }
        return render(request, 'users/password_reset.html', context)

    context = {
        'form': UserPasswordUpdateForm(),
        'user': user[0],
        'title': title,
    }
    return render(request, 'users/password_reset.html', context)

@login_required
@must_be_staff
def update(request, user_id):
    user = User.objects.filter(id=user_id)
    title = _("Update User")

    if user.count() != 1:
        raise Http404
    try:
        user[0].profile
    except:
        profile_exists = False
    else:
        profile_exists = True

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=user[0])
        if profile_exists:
            p_form = ProfileCreateForm(request.POST, instance=user[0].profile)
        else:
            p_form = ProfileCreateForm(request.POST)

        if u_form.is_valid() and p_form.is_valid():
            user = u_form.save()
            profile = p_form.save(commit=False)
            profile.user = user
            profile.save()
            username = u_form.cleaned_data.get('username')
            messages.success(request,
                             _('The account for %(username)s has been updated') %
                             { 'username': username})
            return redirect('lgc-users')
        context = {
            'u_form': u_form,
            'p_form': p_form,
            'update': 1,
            'user_id': user_id,
            'title': title,
        }
        return render(request, 'users/create.html', context)

    if profile_exists:
        p_form = ProfileCreateForm(instance=user[0].profile)
    else:
        p_form = ProfileCreateForm
    context = {
        'u_form': UserUpdateForm(instance=user[0]),
        'p_form': p_form,
        'update': 1,
        'user_id': user_id,
        'title': title,
    }
    return render(request, 'users/create.html', context)

@login_required
@must_be_staff
def profile(request):
    return render(request, 'users/profile.html')

@login_required
def logout_then_login_with_msg(request):
    messages.success(request, _('You were successfully logged-out.'))
    return logout_then_login(request)

@login_required
@must_be_staff
def ajax_view(request):
    term = request.GET.get('term', '')
    users = User.objects.filter(username__istartswith=term)
    users = User.objects.filter(username__istartswith=term)|User.objects.filter(email__istartswith=term)|User.objects.filter(first_name__istartswith=term)|User.objects.filter(last_name__istartswith=term)
    users = users[:10]

    for u in users:
        if term in u.username.lower():
            u.b_username = u.username.lower()
        elif term in u.email.lower():
            u.b_email = u.email.lower()
        elif term in u.first_name.lower():
            u.b_first_name = u.first_name.lower()
        elif term in u.last_name.lower():
            u.b_last_name = u.last_name.lower()
    context = {
        'users': users
    }
    return render(request, 'users/search.html', context)
