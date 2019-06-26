from common.utils import pagination, must_be_staff
from django.http import Http404
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout_then_login, LoginView as authLoginView
from django.contrib.auth import logout
from django.utils.translation import ugettext as _
from django.utils import translation
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from . import forms as user_forms
from lgc import models as lgc_models
from lgc.views import token_generator
from django.views.generic import (ListView, DetailView, CreateView,
                                  UpdateView, DeleteView)
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from ipaddress import IPv4Address, IPv4Network
from . import models as user_models
import os
import logging

log = logging.getLogger('user')
User = get_user_model()

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'lgc/sub_generic_list.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_ordering(self):
        return self.request.GET.get('order_by', '-date_joined')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_queryset(self):
        users = user_models.get_all_local_user_queryset()
        term = self.request.GET.get('term', '')
        order_by = self.get_ordering()
        if term == '':
            return users.order_by(order_by)
        objs = (users.filter(email__istartswith=term)|
                users.filter(first_name__istartswith=term)|
                users.filter(last_name__istartswith=term))
        return objs.order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Users')
        context['create_url'] = reverse_lazy('user-create')
        context['item_url'] = 'user'
        context['ajax_search_url'] = reverse_lazy('user-local-user-search-ajax')
        context['search_url'] = reverse_lazy('user-list')
        context['header_values'] = [
            ('email', 'E-mail'), ('first_name', _('First Name')),
            ('last_name', _('Last Name')), ('is_active', _('Active')),
            ('role', _('Role')), ('billing', _('Billing')),
            ('is_staff', _('Staff'))
        ]

        return pagination(self.request, context, reverse_lazy('user-list'))

class UserCreateView(LoginRequiredMixin, SuccessMessageMixin, UserPassesTestMixin,
                     CreateView):
    model = User
    template_name = 'users/create.html'
    success_message = _('User successfully created.')
    success_url = reverse_lazy('user-create')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('New User')
        return context

    def get_form(self):
        return super().get_form(form_class=user_forms.UserCreateForm)

    def test_func(self):
        return self.request.user.is_staff

class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UserPassesTestMixin,
                     UpdateView):
    model = User
    template_name = 'users/create.html'
    success_message = _('User successfully updated.')

    def get_success_url(self):
        self.object = self.get_object()
        if not self.object.is_staff:
            return reverse_lazy('lgc-home')
        return reverse_lazy('user', kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Update User')
        context['delete_url'] = reverse_lazy('user-delete',
                                             kwargs={'pk': self.object.id})
        context['pw_reset_url'] = reverse_lazy('user-pw-reset',
                                               kwargs={'user_id': self.object.id})
        return context

    def get_form(self):
        return super().get_form(form_class=user_forms.UserUpdateForm)

    def test_func(self):
        return self.request.user.is_staff

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'users/confirm_delete.html'
    success_url = reverse_lazy('user-list')
    title = _('Delete User')
    success_message = _('User successfully deleted.')
    profile_update = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        if not self.profile_update:
            cancel_url = reverse_lazy('user', kwargs={'pk': self.object.id})
            confirm_message = _('Are you sure you want to delete the account of %s %s'%(
                self.object.first_name, self.object.last_name))
        else:
            cancel_url = reverse_lazy('user-profile')
            confirm_message = _('Are you sure you want to delete your account?')
        context['cancel_url'] = cancel_url
        context['profile_update'] = self.profile_update
        context['confirm_message'] = confirm_message
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        if not self.profile_update:
            return super().delete(request, *args, **kwargs)
        obj = self.get_object()
        obj.is_active = False
        obj.status = user_models.USER_STATUS_DELETED_BY_EMPLOYEE
        obj.save()
        return redirect('user-logout')

@login_required
@must_be_staff
def password_reset(request, user_id):
    user = User.objects.filter(id=user_id)
    title = _("Password Reset")
    form = user_forms.UserPasswordUpdateForm()

    if user.count() != 1:
        raise Http404
    if request.method == 'POST':
        form = user_forms.UserPasswordUpdateForm(request.POST,
                                                 instance=user[0])
        if form.is_valid():
            form.save()
            messages.success(request,
                             _('The password for %s %s has been successfully updated') %
                             (user[0].first_name, user[0].last_name))
            return redirect('user', user_id)

    context = {
        'form': form,
        'user': user[0],
        'title': title,
        'cancel_url': reverse_lazy('user', kwargs={'pk': user_id})

    }
    return render(request, 'users/password_reset.html', context)

def return_true(obj):
    return True

@login_required
def profile_delete(request):
    user_delete_view = UserDeleteView
    user_delete_view.title = _('Delete My Account')
    user_delete_view.success_url = reverse_lazy('user-logout')
    user_delete_view.success_message = _('Your account has been successfully deleted.')
    user_delete_view.profile_update = True
    user_delete_view.test_func = return_true
    view = user_delete_view.as_view()
    return view(request, pk=request.user.id)

@login_required
def profile_password_reset(request):
    title = _('Password Reset')
    form = user_forms.UserPasswordUpdateForm()

    if request.method == 'POST':
        form = user_forms.UserPasswordUpdateForm(request.POST,
                                                 instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request,
                             _('Your password has been successfully updated'))
            return redirect('user-profile')

    context = {
        'form': form,
        'title': title,
        'cancel_url': reverse_lazy('user-profile'),
        'profile_update': 1,
    }
    return render(request, 'users/password_reset.html', context)

@login_required
def update_profile(request):
    context = {
        'profile_update': 1,
        'title': _("My Account Profile"),
        'delete_url': reverse_lazy('user-profile-delete'),
        'pw_reset_url': reverse_lazy('user-profile-pw-reset'),
    }

    if request.method == 'POST':
        form = user_forms.UserUpdateProfileForm(request.POST,
                                                instance=request.user)

        if form.is_valid():
            user = form.save()
            if user.language != 'EN' and user.language != 'FR':
                raise Http404

            translation.activate(user.language)
            request.session[translation.LANGUAGE_SESSION_KEY] = user.language
            messages.success(request,
                             _('Your account profile has been updated'))

            if hasattr(user, 'person_user_set'):
                user.person_user_set.first_name = user.first_name
                user.person_user_set.last_name = user.last_name
                user.person_user_set.email = user.email
                user.person_user_set.save()
            return redirect('user-profile')

        context['form'] = form
    else:
        context['form'] = user_forms.UserUpdateProfileForm(instance=request.user)

    return render(request, 'users/create.html', context)

class LoginView(authLoginView):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        url_next = self.request.GET.get('next')

        if not url_next:
            return context

        url_next = url_next[4:]
        urls = [ '', 'user/profile/', 'user/logout/' ]
        for lang in settings.LANGUAGES:
            if url_next in urls:
                return context
        messages.error(self.request, _('Your session has expired.'))
        return context

    def form_valid(self, form):
        form = super().form_valid(form)
        ip = self.request.META.get('REMOTE_ADDR')
        ip = IPv4Address(ip)
        found = False

        for subnet in settings.ALLOWED_SESSION_NOTIMEOUT_SUBNETS:
            if ip in IPv4Network(subnet):
                found = True
                break
        if not found:
            self.request.session.set_expiry(settings.SESSION_EXPIRATION)

        if self.request.user.role in user_models.get_internal_roles():
            return form

        if (self.request.user.password_last_update == None or
            self.request.user.password_last_update + timedelta(days=settings.AUTH_PASSWORD_EXPIRY) < timezone.now().date()):
            messages.error(self.request, _('Your password has expired. Please choose a new one'))
            token = token_generator()
            self.request.user.token = token
            self.request.user.token_date = timezone.now()
            self.request.user.save()
            logout(self.request)
            response = redirect('user-token')
            response['Location'] += '?token=' + token
            return response
        return form

@login_required
def logout_then_login_with_msg(request):
    messages.success(request, _('You were successfully logged-out.'))
    return logout_then_login(request)

def __ajax_view(request, users):
    term = request.GET.get('term', '')
    term = term.lower()
    users = users.filter(email__istartswith=term)|users.filter(first_name__istartswith=term)|users.filter(last_name__istartswith=term)
    users = users[:10]

    for u in users:
        if u.email.lower().startswith(term):
            u.b_email = u.email.lower()
        if u.first_name.lower().startswith(term):
            u.b_first_name = u.first_name.lower()
        if u.last_name.lower().startswith(term):
            u.b_last_name = u.last_name.lower()
    context = {
        'users': users
    }
    return render(request, 'users/search.html', context)

def handle_auth_token(request):
    title = _("Welcome to LGC")
    token = request.GET.get('token', '')
    context = {
        'title': title,
    }

    if token == '':
        return render(request, 'users/token_bad.html', context)

    user = user_models.get_hr_user_queryset().filter(token=token)
    if len(user) == 0:
        user = user_models.get_employee_user_queryset().filter(token=token)
        if len(user) == 0:
            return render(request, 'users/token_bad.html', context)

    user = user.get()
    if user == None or user.token_date + timedelta(hours=settings.AUTH_TOKEN_EXPIRY) < timezone.now():
        return render(request, 'users/token_bad.html', context)

    context['user'] = user
    if request.method == 'POST':
        if user.password == '':
            form = user_forms.UserPasswordUpdateForm(request.POST, instance=user)
        else:
            form = user_forms.UserForcePasswordUpdateForm(request.POST, instance=user)
        context['form'] = form
        terms = request.POST.get('terms', '')

        if not form.is_valid() or terms != '1':
            return render(request, 'users/token.html', context)

        if user.password != '':
            if not check_password(form.cleaned_data['current_password'], form.instance.password):
                messages.error(request, _('The current password does not match.'))
                return render(request, 'users/token.html', context)
            if form.cleaned_data['current_password'] == form.cleaned_data['password1']:
                messages.error(request,
                               _('The new password and the old one must be different.'))
                return render(request, 'users/token.html', context)
        form.instance.token = ''
        form.instance.token_date = None
        form.instance.status = user_models.USER_STATUS_ACTIVE
        form.instance.password_last_update = timezone.now().date()
        form.save()
        if (form.instance.role == user_models.ROLE_EMPLOYEE and
            not hasattr(form.instance, 'person_user_set')):
            p = lgc_models.Person()
            p.first_name = form.instance.first_name
            p.last_name = form.instance.last_name
            p.email = form.instance.email
            p.modified_by = form.instance
            p.user = form.instance
            p.save()
            p.responsible.set(form.instance.responsible.all())
        messages.success(request,
                         _('The password for %s %s has been successfully set') %
                         (user.first_name, user.last_name))
        return redirect('user-login')
    else:
        if user.password == '':
            form = user_forms.UserPasswordUpdateForm()
        else:
            form = user_forms.UserForcePasswordUpdateForm()
        context['form'] = form
    return render(request, 'users/token.html', context)

@login_required
@must_be_staff
def ajax_local_user_seach_view(request):
    users = user_models.get_all_local_user_queryset()
    return __ajax_view(request, users)

@login_required
def ajax_hr_user_seach_view(request):
    if (request.user.role not in user_models.get_hr_roles() +
        user_models.get_internal_roles()):
        return HttpResponseForbidden()
    users = user_models.get_hr_user_queryset()
    return __ajax_view(request, users)

@login_required
def ajax_employee_user_seach_view(request):
    if request.user.role not in user_models.get_internal_roles():
        return HttpResponseForbidden()
    users = user_models.get_employee_user_queryset()
    return __ajax_view(request, users)
