import pdb                # pdb.set_trace()
from django.db import transaction
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from common.utils import (pagination, lgc_send_email, must_be_staff,
                          set_bold_search_attrs)
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
from . import views as lgc_views
from . import models as lgc_models
from . import forms as lgc_forms
from employee import forms as employee_forms
from employee import models as employee_models
from .forms import LgcTab
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
from django.utils.safestring import mark_safe
from common import lgc_types
import string
import random
import datetime
import os

class BillingTest(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        if self.request.user.role not in user_models.get_internal_roles():
            return False
        return self.request.user.billing

class ClientListView(BillingTest, ListView):
    template_name = 'lgc/sub_generic_list.html'
    model = lgc_models.Client
    title = _('Clients')
    create_url = reverse_lazy('lgc-client-create')
    item_url = 'lgc-client'
    this_url = reverse_lazy('lgc-clients')
    ajax_search_url = reverse_lazy('lgc-client-search-ajax')
    search_url = reverse_lazy('lgc-clients')

    def get_queryset(self):
        term = self.request.GET.get('term', '')
        order_by = self.get_ordering()
        if term == '':
            return self.model.objects.order_by(order_by)
        objs = lgc_models.Client.objects
        objs = (objs.filter(email__istartswith=term)|
                objs.filter(first_name__istartswith=term)|
                objs.filter(last_name__istartswith=term)|
                objs.filter(company__istartswith=term))

        return objs.order_by(order_by)

    def get_ordering(self):
        return self.request.GET.get('order_by', 'id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['create_url'] = self.create_url
        context['item_url'] = self.item_url
        context['ajax_search_url'] = self.ajax_search_url
        context['search_url'] = self.search_url
        context['header_values'] = [
            ('ID', 'id'), (_('First Name'), 'first_name'), ('Email', 'email'),
            (_('Company'), 'company')
        ]
        return pagination(self.request, context, self.this_url)

class ClientCreateView(BillingTest, SuccessMessageMixin, CreateView):
    model = lgc_models.Invoice
    title = _('New Client')
    success_message = _('Client successfully created.')
    template_name = 'lgc/generic_form.html'
    success_url = reverse_lazy('lgc-client-create')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def get_form(self, form_class=lgc_forms.ClientCreateForm):
        form = super().get_form(form_class=form_class)
        return form

    def form_valid(self, form):
        if (not form.cleaned_data['first_name'] and
            not form.cleaned_data['last_name'] and
            not form.cleaned_data['company']):
            messages.error(self.request,
                           _('First Name, Last Name and Company cannot be empty together.'))
            return self.form_invalid(form)
        return super().form_valid(form)

class ClientUpdateView(BillingTest, SuccessMessageMixin, UpdateView):
    model = lgc_models.Client
    success_message = _('Client successfully updated')
    success_url = 'lgc-client'
    title = _('Client')
    delete_url = 'lgc-client-delete'
    template_name = 'lgc/generic_form.html'

    def get_success_url(self):
        self.object = self.get_object()
        return reverse_lazy(self.success_url, kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        if self.delete_url != '':
            context['delete_url'] = reverse_lazy(self.delete_url,
                                                 kwargs={'pk':self.object.id})
        return context

    def get_form(self, form_class=lgc_forms.ClientCreateForm):
        return super().get_form(form_class=form_class)

class ClientDeleteView(BillingTest, DeleteView):
    model = lgc_models.Client
    success_url = reverse_lazy('lgc-clients')
    title = _('Delete Client')
    cancel_url = 'lgc-client'
    obj_name = _('Client')
    template_name = 'lgc/person_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['cancel_url'] = reverse_lazy(self.cancel_url,
                                             kwargs={'pk':self.object.id})
        context['dont_inform'] = True
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.first_name and not self.object.last_name:
            name = self.object.company
        else:
            name = self.object.first_name + ' ' + self.object.last_name
        success_message = (_("Client %(name)s successfully deleted."%
                           {'name': name}))
        messages.success(self.request, success_message)
        return super().delete(request, *args, **kwargs)

class InvoiceCreateView(BillingTest, CreateView):
    model = lgc_models.Invoice
    title = _('New Invoice')
    success_message = _('Invoice successfully created')
    template_name = 'lgc/generic_form_with_formsets.html'
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def get_form(self, form_class=lgc_forms.InvoiceCreateForm):
        form = super().get_form(form_class=form_class)
        form.helper = FormHelper()
        layout = Layout(
            Div(Div(HTML('<p><button class="btn btn-primary" type="button" data-toggle="collapse" data-target="#collapsePO" aria-expanded="false" aria-controls="collapsePO">' +
                         _('Authorizations') +'</button></p>'),
                    css_class='form-group col-md-8'),
                css_class='form-row'),
            Div(
                Div(
                    Div('po', css_class='form-group col-md-2'),
                    Div('po_date', css_class='form-group col-md-2'),
                    Div('po_rate', css_class='form-group col-md-2'),
                    css_class='form-row'),
                Div(
                    Div('po_first_name', css_class='form-group col-md-2'),
                    Div('po_last_name', css_class='form-group col-md-2'),
                    Div('po_email', css_class='form-group col-md-2'),
                    css_class='form-row'),
                Div(Div(HTML('<hr>'), css_class='form-group col-md-8'),
                    css_class='form-row'),
                css_class='collapse', id='collapsePO'),
            Div('first_name'), Div('last_name'), Div('company'),
            Div('email'), Div('phone_number'), Div('cell_phone_number'),
            Div('siret'), Div('vat'), Div('address'), Div('post_code'),
            Div('city'), Div('country'), Div('version'),
            Div(
                Div('invoice_date', css_class='form-group col-md-2'),
                Div('modification_date', css_class='form-group col-md-2'),
                Div('payment_option', css_class='form-group col-md-2'),
                Div('currency', css_class='form-group col-md-2'),
                css_class='form-row'),
            Div(
                Div('language', css_class='form-group col-md-2'),
                Div('company_option', css_class='form-group col-md-2'),
                Div('with_regard_to', css_class='form-group col-md-2'),
                Div('various_expenses',
                    css_class='form-group col-md-2 lgc_aligned_checkbox'),
                css_class='form-row'),
            Div(
                Div('state', css_class='form-group col-md-2'),
                Div('already_paid', css_class='form-group col-md-2'),
                css_class='form-row'),
        )
        form.helper.layout = layout
        return form

@login_required
def ajax_client_search_view(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()
    if not request.user.billing:
        return http.HttpResponseForbidden()

    term = request.GET.get('term', '')
    objs = lgc_models.Client.objects
    objs = (objs.filter(email__istartswith=term)|
            objs.filter(first_name__istartswith=term)|
            objs.filter(last_name__istartswith=term)|
            objs.filter(company__istartswith=term))
    set_bold_search_attrs(objs, term, ['first_name', 'last_name', 'company'])
    objs = objs[:10]
    context = {
        'objects': objs
    }
    return render(request, 'lgc/client_search.html', context)
