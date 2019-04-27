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
from . import forms as employee_forms
from lgc import forms as lgc_forms
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
from . import models as employee_models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from common import lgc_types
import string
import random
import datetime
import os, pdb

User = get_user_model()

class PersonUpdateView(lgc_views.PersonUpdateView):
    model = employee_models.Employee

    def get_success_url(self):
        return reverse_lazy('employee-file')

def my_file(request):
    if not hasattr(request.user, 'employee_user_set'):
        employee = employee_models.Employee()
        employee.first_name = request.user.first_name
        employee.last_name = request.user.last_name
        employee.email = request.user.email
        employee.user = request.user
        employee.modified_by = request.user
        employee.save()
    view = PersonUpdateView.as_view()
    return view(request, pk=request.user.employee_user_set.id)

@login_required
def my_expirations(request):
    if request.user.role != user_models.EMPLOYEE:
        return http.HttpResponseForbidden()

    form = lgc_views.get_expirations_form(request)

    """ remove the user field """
    del form.fields['user']
    form.helper.layout[0].pop(0)

    objs = lgc_models.Expiration.objects.filter(person=request.user.person_user_set)
    objs = lgc_views.expirations_filter_objs(request, objs)
    return lgc_views.__expirations(request, form, objs)

def paginate_moderations(request, object_list):
    paginate = request.GET.get('paginate', 10)
    order_by = request.GET.get('order_by', 'id')
    object_list = object_list.order_by(order_by)
    paginator = Paginator(object_list, paginate)
    page = request.GET.get('page')
    return paginator.get_page(page)

@login_required
def moderations(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    context = {
        'title': 'Moderations',
    }
    context = pagination(request, context, reverse_lazy('employee-moderations'))
    objs = employee_models.Employee.objects.filter(updated=True)
    context['page_obj'] = paginate_moderations(request, objs)

    if (len(objs) and (context['page_obj'].has_next() or
                       context['page_obj'].has_previous())):
        context['is_paginated'] = True
    else:
        context['is_paginated'] = False
    context['header_values'] = [('ID', 'id'), (_('First name'), 'first_name'),
                                (_('Last name'), 'last_name'),
                                (_('E-mail'), 'email'),
                                (_('Host entity'), 'host_entity'),]
    context['object_list'] = context['page_obj'].object_list
    context['dont_show_search_bar'] = True
    context['item_url'] = 'employee-moderation'

    return render(request, 'lgc/sub_generic_list.html', context)

@login_required
def moderation(request, *args, **kwargs):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    pk = kwargs.get('pk', '')
    if pk == '':
        raise Http404

    obj = employee_models.Employee.objects.filter(id=pk)
    if obj == None or len(obj) != 1:
        raise Http404
    obj = obj[0]

    if request.POST:
        person_form = employee_forms.ModerationPersonCreateForm(request.POST,
                                                                instance=obj.user.person_user_set)
        employee_form = employee_forms.ModerationEmployeeUpdateForm(request.POST,
                                                                    instance=obj)
        if person_form.is_valid() and employee_form.is_valid():
            if person_form.cleaned_data['version'] == obj.user.person_user_set.version:
                if employee_form.cleaned_data['version'] != obj.version:
                    messages.error(request, _('Form modified by %(firstname)s %(lastname)s.'%{
                        'firstname':obj.modified_by.first_name,
                        'lastname': obj.modified_by.last_name
                    }))
                else:
                    employee_form.instance.version += 1
                    employee_form.instance.updated = False
                    employee_form.save()
                    person_common_view = lgc_views.PersonCommonView()
                    person_common_view.copy_related_object(employee_form.instance,
                                                           obj.user.person_user_set,
                                                           employee_form.instance)
                    obj.user.person_user_set.version += 1
                    obj.user.person_user_set.save()
                    messages.success(request, _('Moderation successfully submitted.'))
            else:
                messages.error(request, _('Form modified by %(firstname)s %(lastname)s.'%{
                    'firstname':obj.user.person_user_set.modified_by.first_name,
                    'lastname': obj.user.person_user_set.modified_by.last_name
                }))
    else:
        person_form = employee_forms.ModerationPersonCreateForm(instance=obj.user.person_user_set)
        employee_form = employee_forms.ModerationEmployeeUpdateForm(instance=obj)
    context = {
        'title': 'Moderation',
        'employee_form': employee_form,
        'person_form': person_form,
    }

    return render(request, 'employee/moderation.html', context)
