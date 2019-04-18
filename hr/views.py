import pdb                # pdb.set_trace()
from django.db import transaction
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from common.utils import pagination, lgc_send_email, must_be_staff
import common.utils as common_utils
from django import http
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.core.paginator import Paginator
from django.utils import translation
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin

from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  DeleteView)
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from lgc import models as lgc_models, views as lgc_views
from . import forms as hr_forms
from lgc.forms import LgcTab
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, Button, Row, HTML, MultiField
from crispy_forms.bootstrap import (
    Accordion, AccordionGroup, Alert, AppendedText, FieldWithButtons,
    InlineCheckboxes, InlineRadios, PrependedAppendedText, PrependedText,
    StrictButton, Tab, TabHolder
)
from pathlib import Path
from django.http import Http404
from django.core.exceptions import PermissionDenied
from users import models as user_models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from common import lgc_types
import string
import random
import datetime
import os

User = get_user_model()

class CommonAccountByHR(LoginRequiredMixin, UserPassesTestMixin,
                        SuccessMessageMixin):
    uid = None
    template_name = 'lgc/generic_form_with_formsets.html'
    model = User
    is_update = False
    success_url = 'hr-update-account'
    delete_url = 'lgc-account-delete'
    update_url = 'hr-update-account'
    cancel_url = 'hr-update-account'
    list_url = reverse_lazy('hr-employees')

    def hr_admin_get_initiate_form(self, form, action, uid):
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Div(
                Div('first_name', css_class='form-group col-md-4'),
                Div('last_name', css_class='form-group col-md-4'),
                css_class='form-row'),
            Div(
                Div('email', css_class='form-group col-md-4'),
                Div('language', css_class='form-group col-md-4'),
                css_class='form-row'),
            Div(
                Div('is_active', css_class='form-group col-md-4'),
                css_class='form-row'),
            Div(
                Div('new_token', css_class='form-group col-md-4'),
                css_class='form-row'),
            HTML('<button class="btn btn-outline-info" type="submit">' +
                 action + '</button>')
        )
        if uid:
            form.helper.layout.append(
                HTML(' <a href="{% url "hr-delete-account" ' + str(uid) +
                     '%}" class="btn btn-outline-danger">' +
                     lgc_views.delete_str +
                     '</a>')
            )
        return form

    def test_func(self):
        if self.request.user.role not in user_models.get_hr_roles():
            return False

        try:
            self.object = self.get_object()
            return self.object in self.request.user.hr_employees.all()
        except:
            """ only the HR admin can initiate new cases """
            return self.request.user.role == user_models.HR_ADMIN

    def get_success_url(self):
        return reverse_lazy('hr-update-account', kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def get_form(self, form_class=hr_forms.HRInitiateEmployeeAccountForm):
        form = super().get_form(form_class=form_class)
        return self.hr_admin_get_initiate_form(form, self.submit_button_label,
                                               self.uid)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        form.instance.role = user_models.EMPLOYEE
        if form.cleaned_data['new_token']:
            form.instance.token = lgc_views.token_generator()
            form.instance.token_date = timezone.now()
            try:
                lgc_send_email(self.object, lgc_types.MsgType.NEW_EM)
            except Exception as e:
                messages.error(self.request, _('Cannot send email to') + '`'
                               + self.object.email + '`: ' + str(e))
                return super().form_invalid(form)

        self.object = form.save()

        if not self.is_update:
            form.instance.responsible.set(self.request.user.responsible.all())
            self.request.user.hr_employees.add(self.object)

        return super().form_valid(form)

class InitiateAccountByHR(CommonAccountByHR, CreateView):
    success_message = _('New account successfully initiated')
    title = _('Initiate an account')
    submit_button_label = _('Initiate account')

    def get_form(self, form_class=hr_forms.HRInitiateEmployeeAccountForm):
        form = super().get_form(form_class=form_class)
        return self.hr_admin_get_initiate_form(form, self.submit_button_label,
                                               None)

class UpdateAccountByHR(CommonAccountByHR, UpdateView):
    success_message = _('Account successfully updated')
    title = _('Update Account')
    submit_button_label = _('Update')
    is_update = True

    def get_form(self, form_class=hr_forms.HRInitiateEmployeeAccountForm):
        form = super().get_form(form_class=form_class)
        return self.hr_admin_get_initiate_form(form, self.submit_button_label,
                                               self.object.id)

class HRPersonListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    update_url = 'hr-update-account'
    model = User
    template_name = 'hr/employees.html'

    def get_ordering(self):
        return self.request.GET.get('order_by', '-id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_url'] = reverse_lazy('hr-employees')
        context['title'] = _('Employees')
        context['update_url'] = 'hr-update-account'

        return pagination(self.request, context, reverse_lazy('hr-employees'))

    def test_func(self):
        return self.request.user.role in user_models.get_hr_roles()

    def get_queryset(self):
        term = self.request.GET.get('term', '')

        order_by = self.get_ordering()
        objs = self.request.user.hr_employees.all().exclude(status__in=user_models.get_user_deleted_statuses())

        if term:
            objs = (objs.filter(email__istartswith=term)|
                    objs.filter(first_name__istartswith=term)|
                    objs.filter(last_name__istartswith=term))
        return objs.order_by(order_by)

class HRDeleteAccountView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'lgc/person_confirm_delete.html'
    success_url = reverse_lazy('hr-employees')
    title = _('Delete Account')
    cancel_url = 'hr-update-account'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['cancel_url'] = reverse_lazy(self.cancel_url,
                                             kwargs={'pk':self.object.id})
        return context

    def test_func(self):
        self.object = self.get_object()
        if self.request.user.role not in user_models.get_hr_roles():
            return False
        return self.object in self.request.user.hr_employees.all()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_message = (_("Account of %(first_name)s %(last_name)s successfully deleted.")%
                           {'first_name':self.object.first_name,
                            'last_name':self.object.last_name})
        messages.success(self.request, success_message)
        self.object.status = user_models.USER_STATUS_DELETED_BY_HR
        self.object.save()
        return redirect('hr-employees')

@login_required
def hr_expirations(request):
    if request.user.role not in user_models.get_hr_roles():
        return http.HttpResponseForbidden()

    form = lgc_views.get_expirations_form(request)
    form.fields['user'].label = _('Employee')
    form.fields['user'].queryset = User.objects.filter(id__in=request.user.hr_employees.all())

    persons = []
    for u in request.user.hr_employees.all():
        if hasattr(u, 'person_user_set'):
            persons.append(u.person_user_set)
    objs = lgc_models.Expiration.objects.filter(person__in=persons)
    objs = lgc_views.expirations_filter_objs(request, objs)

    user = request.GET.get('user', None)
    if user:
        user = User.objects.filter(id=user)
        if len(user) != 1:
            raise Http404
        if hasattr(user[0], 'person_user_set'):
            objs = objs.filter(person=user[0].person_user_set)
        else:
            objs = None

    return lgc_views.__expirations(request, form, objs)
