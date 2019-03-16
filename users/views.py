from common.utils import pagination, must_be_staff
from django.http import Http404
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout_then_login
from django.utils.translation import ugettext as _
from django.utils import translation
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from . import forms as user_forms
from lgc import models as lgc_models
from django.views.generic import (ListView, DetailView, CreateView,
                                  UpdateView, DeleteView)
from django.utils import timezone
from django.conf import settings
from datetime import datetime,timedelta
from . import models as user_models
User = get_user_model()

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
        users = user_models.get_local_user_queryset()
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
        order_by = self.get_ordering()
        context['title'] = _("Users")

        return pagination(self, context, reverse_lazy('lgc-users'))

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'users/confirm_delete.html'
    success_url = reverse_lazy('lgc-users')
    success_message = _('User deleted successfully.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete User')
        context['object'] = self.object
        if self.object.role in user_models.get_hr_roles():
            context['cancel_url'] = reverse_lazy('lgc-hr',
                                             kwargs={'pk': self.object.id})
        elif self.object.role == user_models.EMPLOYEE:
            context['cancel_url'] = reverse_lazy('lgc-account',
                                             kwargs={'pk': self.object.id})
        else:
            context['cancel_url'] = reverse_lazy('lgc-user',
                                             kwargs={'user_id': self.object.id})
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
        form = user_forms.UserCreateForm(request.POST)

        if form.is_valid():
            user = form.save()
            email = form.cleaned_data.get('email')
            messages.success(request,
                             _('The account for %(email)s has been created') %
                             { 'email': email})
            return redirect('lgc-user-create')
        context = {
            'form': form,
            'title': title,
        }
        return render(request, 'users/create.html', context)

    context = {
        'form': user_forms.UserCreateForm(),
        'title': title,
    }
    return render(request, 'users/create.html', context)

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
            return redirect('lgc-user', user[0].id)

    context = {
        'form': form,
        'user': user[0],
        'title': title,
    }
    return render(request, 'users/password_reset.html', context)

@login_required
def profile_password_reset(request):
    title = _("Password Reset")
    form = user_forms.UserPasswordUpdateForm()

    if request.method == 'POST':
        form = user_forms.UserPasswordUpdateForm(request.POST,
                                                 instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request,
                             _('Your password has been successfully updated'))
            return redirect('lgc-profile')

    context = {
        'form': form,
        'title': title,
        'profile': 1,
    }
    return render(request, 'users/password_reset.html', context)

@login_required
@must_be_staff
def update(request, user_id):
    user = User.objects.filter(id=user_id)
    title = _("Update User")

    if user.count() != 1:
        raise Http404

    if request.method == 'POST':
        form = user_forms.UserUpdateForm(request.POST, instance=user[0])

        if form.is_valid():
            user = form.save()
            messages.success(request,
                             _('The account of %(first_name)s %(last_name)s has been updated') %
                             { 'first_name': user.first_name,
                               'last_name' : user.last_name })
            return redirect('lgc-users')
        context = {
            'form': form,
            'update': 1,
            'user_id': user_id,
            'title': title,
        }
        return render(request, 'users/create.html', context)

    context = {
        'form': user_forms.UserUpdateForm(instance=user[0]),
        'update': 1,
        'user_id': user_id,
        'title': title,
    }
    return render(request, 'users/create.html', context)

@login_required
def update_profile(request):
    title = _("My Account Profile")

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
            return redirect('lgc-profile')

        context = {
            'form': form,
            'update': 1,
            'user_id': request.user.id,
            'title': title,
        }
        return render(request, 'users/create.html', context)

    context = {
        'form': user_forms.UserUpdateProfileForm(instance=request.user),
        'update': 1,
        'profile' : 1,
        'user_id': request.user.id,
        'title': title,
    }
    return render(request, 'users/create.html', context)

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
        elif u.first_name.lower().startswith(term):
            u.b_first_name = u.first_name.lower()
        elif u.last_name.lower().startswith(term):
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
    if user == None:
        return render(request, 'users/token_bad.html', context)
    if user.token_date + timedelta(hours=settings.AUTH_TOKEN_EXPIRY) < timezone.now():
        return render(request, 'users/token_bad.html', context)

    context['user'] = user
    if request.method == 'POST':
        form = user_forms.UserPasswordUpdateForm(request.POST, instance=user)
        terms = request.POST.get('terms', '')
        if form.is_valid() and terms == '1':
            form.instance.token = ''
            form.instance.token_date = None
            form.save()
            if not hasattr(form.instance, 'person_user_set'):
                p = lgc_models.Person()
                p.first_name = form.instance.first_name
                p.last_name = form.instance.last_name
                p.email = form.instance.email
                p.modified_by = form.instance
                p.user = form.instance
                p.save()
            messages.success(request,
                             _('The password for %s %s has been successfully set') %
                             (user.first_name, user.last_name))
            return redirect('lgc-login')
    else:
        form = user_forms.UserPasswordUpdateForm()
    context['form'] = form
    return render(request, 'users/token.html', context)

@login_required
@must_be_staff
def ajax_local_user_seach_view(request):
    users = user_models.get_local_user_queryset()
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
