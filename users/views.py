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
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .forms import UserCreateForm, UserUpdateForm, UserPasswordUpdateForm
from django.views.generic import (ListView, DetailView, CreateView,
                                  UpdateView, DeleteView)
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
        form = UserCreateForm(request.POST)

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
        'form': UserCreateForm(),
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
                             _('The password for %s %s has been successfully updated') %
                             (user[0].first_name, user[0].last_name))
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

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user[0])

        if form.is_valid():
            user = form.save()
            email = form.cleaned_data.get('email')
            messages.success(request,
                             _('The account of %(email)s has been updated') %
                             { 'email': email})
            return redirect('lgc-users')
        context = {
            'form': form,
            'update': 1,
            'user_id': user_id,
            'title': title,
        }
        return render(request, 'users/create.html', context)

    context = {
        'form': UserUpdateForm(instance=user[0]),
        'update': 1,
        'user_id': user_id,
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
