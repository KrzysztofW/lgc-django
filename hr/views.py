import pdb                # pdb.set_trace()
from django.db import transaction
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from common.utils import pagination, lgc_send_email, must_be_staff
import common.utils as common_utils
from django import http
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy, ugettext as _
from django.core.paginator import Paginator
from django.utils import translation
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin

from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  DeleteView)
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from lgc import models as lgc_models, views as lgc_views
from users import views as user_views
from employee import models as employee_models
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
import logging

log = logging.getLogger('hr')

User = get_user_model()

@login_required
def initiate_case(request):
    context = {
        'title': _('Initiate a case'),
    }
    if request.user.role != user_models.ROLE_HR_ADMIN:
        return http.HttpResponseForbidden()
    if request.method == 'POST':
        failed = False
        form = hr_forms.InitiateCaseForm(request.POST)
        if not form.is_valid():
            messages.error(request, _('Your request contains errors.'))
        else:
            form.hr = request.user
            for u in request.user.responsible.all():
                try:
                    lgc_send_email(form, lgc_types.MsgType.HR_INIT_ACCOUNT, u)
                except Exception as e:
                    if failed:
                        continue
                    messages.error(request,
                                   _('Cannot send the request of the account creation. Please contact the KWA team.'))
                    log.error(e)
                    failed = True

        if not failed:
            return render(request, 'hr/initiate_case_success.html', context)
    else:
        form = hr_forms.InitiateCaseForm()
    form.helper = FormHelper()
    form.helper.form_tag = False
    context['form'] = form
    return render(request, 'hr/initiate_case.html', context)

class PersonUpdateView(lgc_views.PersonUpdateView):
    model = employee_models.Employee
    title = ugettext_lazy('Employee File')

    def get_success_url(self):
        return reverse_lazy('hr-employee-file', kwargs={'pk':self.object.id})

class HRPersonListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    update_url = 'hr-update-account'
    model = User
    template_name = 'hr/employees.html'

    def get_ordering(self):
        return self.request.GET.get('order_by', '-id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_search_form(self):
        if len(self.request.GET):
            form = hr_forms.EmployeeSearchForm(self.request.GET)
        else:
            form = hr_forms.EmployeeSearchForm()

        form.helper = FormHelper()
        form.helper.form_tag = False
        form.helper.form_method = 'get'
        form.helper.layout = Layout(
            Div(
                Div('first_name', css_class='form-group col-md-2'),
                Div('last_name', css_class='form-group col-md-2'),
                Div('home_entity', css_class='form-group col-md-2'),
                Div('host_entity', css_class='form-group col-md-2'),
                css_class='form-row'),
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_url'] = reverse_lazy('hr-employees')
        context['title'] = _('Employees')
        context['update_url'] = 'hr-update-account'
        context['item_url'] = 'hr-employee-file'
        context['search_form'] = self.get_search_form()

        return pagination(self.request, context, reverse_lazy('hr-employees'))

    def test_func(self):
        return self.request.user.role in user_models.get_hr_roles()

    def match_extra_terms(self, objs):
        first_name = self.request.GET.get('first_name')
        last_name = self.request.GET.get('last_name')
        email = self.request.GET.get('email')
        home_entity = self.request.GET.get('home_entity')
        host_entity = self.request.GET.get('host_entity')

        if home_entity:
            objs = objs.filter(employee_user_set__home_entity__istartswith=home_entity)
        if host_entity:
            objs = objs.filter(employee_user_set__host_entity__istartswith=host_entity)
        if first_name:
            objs = objs.filter(first_name__istartswith=first_name)
        if last_name:
            objs = objs.filter(last_name__istartswith=last_name)
        return objs

    def get_queryset(self):
        term = self.request.GET.get('term')
        order_by = self.get_ordering()
        objs = self.match_extra_terms(self.request.user.hr_employees.exclude(status__in=user_models.get_user_deleted_statuses()))

        if term:
            objs = (objs.filter(email__istartswith=term)|
                    objs.filter(first_name__istartswith=term)|
                    objs.filter(last_name__istartswith=term))

        return objs.order_by(order_by)

def get_expirations_form(request):
    if len(request.GET):
        form = hr_forms.ExpirationSearchForm(request.GET)
    else:
        form = hr_forms.ExpirationSearchForm()
        form.fields['expires'].initial = settings.EXPIRATIONS_NB_DAYS
    form.helper = FormHelper()
    form.helper.form_method = 'get'
    form.helper.layout = Layout(
        Div(
            Div('first_name', css_class='form-group col-md-3'),
            Div('last_name', css_class='form-group col-md-3'),
            Div('expires', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(
            Div('show_disabled', css_class='form-group col-md-3 lgc_aligned_checkbox'),
            Div('show_expired', css_class='form-group col-md-3 lgc_aligned_checkbox'),
            Div(HTML('<button class="btn btn-outline-info" type="submit">' +
                     str(_('Search')) + '</button>')),
            css_class='form-row'),
    )

    return form

@login_required
def hr_expirations(request):
    if request.user.role not in user_models.get_hr_roles():
        return http.HttpResponseForbidden()

    form = get_expirations_form(request)
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
