import pdb                # pdb.set_trace()
from django.db import transaction
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from common.utils import (pagination, lgc_send_email, must_be_staff,
                          set_bold_search_attrs, get_template)
from common.session_cache import session_cache_add, session_cache_get
import common.utils as common_utils
from django import http
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
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
from django.db.models import Max
from common import lgc_types
import string
import random
import datetime
import subprocess
import os
import logging

log = logging.getLogger('lgc')

User = get_user_model()
CURRENT_DIR = Path(__file__).parent

class BillingTestLocalUser(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in user_models.get_internal_roles()

class BillingTest(BillingTestLocalUser):
    def test_func(self):
        if not super().test_func():
            return False
        return self.request.user.billing

class ClientListView(BillingTestLocalUser, ListView):
    template_name = 'lgc/sub_generic_list.html'
    model = lgc_models.Client
    title = ugettext_lazy('Clients')
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
            ('id', 'ID'), ('first_name', _('First Name')),
            ('last_name', _('Last Name')),
            ('company', _('Company')), ('email', 'Email'),
        ]
        return pagination(self.request, context, self.this_url)

class ClientCommonView(BillingTestLocalUser, SuccessMessageMixin):
    model = lgc_models.Client
    template_name = 'lgc/generic_form_with_formsets.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def get_form(self, form_class=lgc_forms.ClientCreateForm):
        form = super().get_form(form_class=form_class)
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Div(
                Div('first_name', css_class='form-group col-md-3'),
                Div('last_name', css_class='form-group col-md-3'),
                Div('company', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(
                Div('email', css_class='form-group col-md-3'),
                Div('phone_number', css_class='form-group col-md-3'),
                Div('cell_phone_number', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(
                Div('siret', css_class='form-group col-md-3'),
                Div('vat', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(
                Div('address', css_class='form-group col-md-3'),
                Div('post_code', css_class='form-group col-md-3'),
                Div('city', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(
                Div('country', css_class='form-group col-md-3'),
                css_class='form-row'),

            Div(Div(HTML('<hr>'), css_class='form-group col-md-9'),
                css_class='form-row'),
            Div(Div(HTML('<h4>'+ _('Billing Address') +'</h4>'),
                    css_class='form-group col-md-9'),
                css_class='form-row'),
            Div(
                Div('billing_company', css_class='form-group col-md-3'),
                Div('billing_address', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(
                Div('billing_post_code', css_class='form-group col-md-3'),
                Div('billing_city', css_class='form-group col-md-3'),
                Div('billing_country', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(Div(HTML('<hr>'), css_class='form-group col-md-9'),
                css_class='form-row'),
        )
        if self.object:
            action = _('Update')
            delete_btn = HTML('&nbsp;<a href="' +
                              str(reverse_lazy('lgc-client-delete',
                                               kwargs={'pk':self.object.id})) +
                              '" class="btn btn-outline-info">' +
                              _('Delete') + '</a>')
        else:
            action = _('Create')
            delete_btn = None
        form.helper.layout.append(HTML('<button class="btn btn-outline-info" type="submit">' +
                                        action + '</button>'))
        form.helper.layout.append(delete_btn)
        return form

    def form_valid(self, form):
        if (not form.cleaned_data['first_name'] and
            not form.cleaned_data['last_name'] and
            not form.cleaned_data['company']):
            messages.error(self.request,
                           _('First Name, Last Name and Company cannot be empty together.'))
            return self.form_invalid(form)
        return super().form_valid(form)

class ClientCreateView(ClientCommonView, CreateView):
    title = ugettext_lazy('New Client')
    success_message = ugettext_lazy('Client successfully created.')
    success_url = reverse_lazy('lgc-client-create')

class ClientUpdateView(ClientCommonView, UpdateView):
    title = ugettext_lazy('Client')
    success_message = ugettext_lazy('Client successfully updated.')
    success_url = 'lgc-client'
    delete_url = 'lgc-client-delete'

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
    title = ugettext_lazy('Delete Client')
    cancel_url = 'lgc-client'
    obj_name = ugettext_lazy('Client')
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

class InvoiceListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'lgc/sub_generic_list_with_search_form.html'
    model = lgc_models.Invoice
    title = ugettext_lazy('Invoices')
    item_url = 'lgc-invoice'
    this_url = reverse_lazy('lgc-invoices')
    ajax_search_url = reverse_lazy('lgc-invoice-search-ajax')
    search_url = reverse_lazy('lgc-invoices')
    objs = lgc_models.Invoice.objects.filter(type=lgc_models.INVOICE)
    invoice_type = lgc_models.INVOICE

    def test_func(self):
        return (self.request.user.role == user_models.ROLE_CONSULTANT or
                self.request.user.billing)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Range totals"""
        self.eur = {
            'items': 0.,
            'items_vat': 0.,
            'disbursements': 0.,
            'disbursements_vat': 0.,
        }
        self.usd = {
            'items': 0.,
            'items_vat': 0.,
            'disbursements': 0.,
            'disbursements_vat': 0.,
        }
        self.cad = {
            'items': 0.,
            'items_vat': 0.,
            'disbursements': 0.,
            'disbursements_vat': 0.,
        }
        self.gbp = {
            'items': 0.,
            'items_vat': 0.,
            'disbursements': 0.,
            'disbursements_vat': 0.,
        }

    def get_search_form(self):
        if len(self.request.GET):
            """Set default cols if none in GET."""
            if (not self.request.GET.get('cols') or
                not self.request.GET.get('csv')):
                self.request.GET = self.request.GET.copy()

                if not self.request.GET.get('cols'):
                    self.request.GET.setlist('cols', lgc_forms.InvoiceSearchForm.default_cols)
                if not self.request.GET.get('csv'):
                    self.request.GET.setlist('csv', lgc_forms.InvoiceSearchForm.default_csv_cols)

            form = lgc_forms.InvoiceSearchForm(self.request.GET)
        else:
            form = lgc_forms.InvoiceSearchForm()

        csv_div = None
        csv_html = None

        if self.invoice_type == lgc_models.QUOTATION:
            form.fields['state'].choices = lgc_models.QUOTATION_STATE_CHOICES
            form.fields['cols'].choices = lgc_forms.QUOTATION_SEARCH_COLS_CHOICES
        else:
            form.fields['state'].choices = lgc_models.INVOICE_STATE_CHOICES
            if self.request.user.billing:
                csv_div = Div('csv', css_class='form-group col-md-4')
                csv_html = Div(Div(HTML('<label class="col-form-label">&nbsp;</label>'),
                                   Div(HTML('<a href="#" onclick="submit_csv();">' +
                                            _('Export') + '</a>')),
                                   css_class="form-group"), css_class='form-group col-md-3')
        form.fields['state'].choices = [('', '---------')] + form.fields['state'].choices

        if self.request.user.billing:
            cols_div = Div('cols', css_class='form-group col-md-3')
            resp_div = Div('responsible', css_class='form-group col-md-3')
            total_div = Div('total', css_class='form-group col-md-3')
        else:
            cols_div = None
            resp_div = None
            total_div = None
        form.helper = FormHelper()
        form.helper.form_tag = False
        form.helper.form_method = 'get'
        form.helper.layout = Layout(
            Div(
                Div('is_csv'),
                Div('number', css_class='form-group col-md-3'),
                Div('state', css_class='form-group col-md-3'),
                resp_div,
                Div('currency', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(
                Div('dates', css_class='form-group col-md-3') if self.invoice_type != lgc_models.QUOTATION else None,
                Div('sdate', css_class='form-group col-md-3'),
                Div('edate', css_class='form-group col-md-3'),
                total_div,
                css_class='form-row'),
            Div(
                cols_div, csv_div, csv_html, css_class='form-row'),
        )
        return form

    def match_extra_terms(self, objs, term):
        number = self.request.GET.get('number')
        state = self.request.GET.get('state')
        currency = self.request.GET.get('currency')
        responsible = self.request.GET.get('responsible')
        start_date = self.request.GET.get('sdate')
        end_date = self.request.GET.get('edate')
        dates = self.request.GET.get('dates')
        total = self.request.GET.get('total')
        do_range_total = False
        search_query = str(term)

        if number:
            number = number.lower().strip('fa')
            number = number.strip('av')
            number = number.strip('de')
            try:
                nb = int(number)
                objs = objs.filter(number=nb)
                search_query += number
            except:
                return objs.none()
        if state:
            objs = objs.filter(state=state)
            search_query += state
        if currency:
            objs = objs.filter(currency=currency)
            search_query += currency
        if total:
            objs = objs.filter(total=total)
            search_query += total
        if responsible:
            o = User.objects.filter(id=responsible)
            search_query += responsible
            if len(o):
                objs = objs.filter(person__responsible__in=o)

        search_query += str(dates)
        if dates == lgc_forms.INVOICE_SEARCH_DATE_INVOICE:
            if start_date and end_date:
                do_range_total = True
                objs = objs.filter(invoice_date__range=[common_utils.parse_date(start_date),
                                                        common_utils.parse_date(end_date)])
            elif start_date:
                objs = objs.filter(invoice_date__gte=common_utils.parse_date(start_date))
            elif end_date:
                objs = objs.filter(invoice_date__lte=common_utils.parse_date(end_date))
        elif (self.invoice_type != lgc_models.QUOTATION and
              (start_date or end_date)):
            objs = objs.filter(state=lgc_models.INVOICE_STATE_PAID)
            if start_date and end_date:
                do_range_total = True
                objs = objs.filter(last_modified_date__range=[common_utils.parse_date(start_date),
                                                        common_utils.parse_date(end_date)])
            elif start_date:
                objs = objs.filter(last_modified_date__gte=common_utils.parse_date(start_date))
            elif end_date:
                objs = objs.filter(last_modified_date__lte=common_utils.parse_date(end_date))
        if do_range_total:
            key = start_date + end_date
            val = session_cache_get(self.request.session, key)
            if val and val['search_query'] == search_query:
                self.eur = val['eur']
                self.usd = val['usd']
                self.cad = val['cad']
                self.gbp = val['gbp']
                return objs

            if len(objs) > 4000:
                messages.error(self.request,
                               _('The number of selected invoices is greater than 4000.'))
                return objs
            for o in objs:
                if o.currency == 'EUR':
                    self.eur['items'] += o.get_total_items
                    self.eur['items_vat'] += o.get_total_items_vat
                    if self.invoice_type == lgc_models.INVOICE:
                        self.eur['disbursements'] += o.get_total_disbursements
                        self.eur['disbursements_vat'] += o.get_total_disbursements_vat
                elif o.currency == 'USD':
                    self.usd['items'] += o.get_total_items
                    self.usd['items_vat'] += o.get_total_items_vat
                    if self.invoice_type == lgc_models.INVOICE:
                        self.usd['disbursements'] += o.get_total_disbursements
                        self.usd['disbursements_vat'] += o.get_total_disbursements_vat
                if o.currency == 'CAD':
                    self.cad['items'] += o.get_total_items
                    self.cad['items_vat'] += o.get_total_items_vat
                    if self.invoice_type == lgc_models.INVOICE:
                        self.cad['disbursements'] += o.get_total_disbursements
                        self.cad['disbursements_vat'] += o.get_total_disbursements_vat
                if o.currency == 'GBP':
                    self.gbp['items'] += o.get_total_items
                    self.gbp['items_vat'] += o.get_total_items_vat
                    if self.invoice_type == lgc_models.INVOICE:
                        self.gbp['disbursements'] += o.get_total_disbursements
                        self.gbp['disbursements_vat'] += o.get_total_disbursements_vat
            cache_val = {
                'eur': self.eur.copy(),
                'usd': self.usd.copy(),
                'cad': self.cad.copy(),
                'gbp': self.gbp.copy(),
                'search_query': search_query,
            }
            session_cache_add(self.request.session, key, cache_val, 1)

        return objs

    def get_queryset(self):
        term = self.request.GET.get('term', '')
        order_by = self.get_ordering()
        if not self.request.user.billing and not self.request.user.is_staff:
            objs = self.objs.filter(person__responsible=self.request.user)
        else:
            objs = self.objs

        if term == '':
            objs = objs.order_by(order_by)
        else:
            objs = (objs.filter(person__first_name__istartswith=term)|
                    objs.filter(person__last_name__istartswith=term)|
                    objs.filter(person__home_entity__istartswith=term)|
                    objs.filter(person__host_entity__istartswith=term)|
                    objs.filter(first_name__istartswith=term)|
                    objs.filter(last_name__istartswith=term)|
                    objs.filter(company__istartswith=term))
            try:
                term_int = int(term)
                objs = objs.filter(number=term_int)
            except:
                pass
        objs = self.match_extra_terms(objs, term)
        return objs.order_by(order_by)

    def get_ordering(self):
        return self.request.GET.get('order_by', '-id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def csv_view(self, request):
        if not self.request.user.billing:
            return http.HttpResponseForbidden()

        start_date = self.request.GET.get('sdate')
        end_date = self.request.GET.get('edate')
        if not start_date or not end_date:
            raise Http404
        if self.request.GET.get('cn'):
            invoice_type = lgc_models.CREDIT
        else:
            invoice_type = lgc_models.INVOICE

        self.objs = lgc_models.Invoice.objects.filter(type=invoice_type)
        objs = self.get_queryset()
        if len(objs) > 4000:
            raise Http404('Too many objects')

        csv = ''
        param_list = []
        dummy_invoice = lgc_models.Invoice()
        for param in self.request.GET.getlist('csv'):
            for c in lgc_forms.INVOICE_SEARCH_CSV_CHOICES:
                if param == c[0] and hasattr(dummy_invoice, param):
                    csv += c[1] + ';'
                    param_list.append(c[0])
                    break
        csv += '\n'
        for o in objs:
            for param in param_list:
                val = getattr(o, param)
                if val == None:
                    val = ''
                elif type(val).__name__ == 'str':
                    val = '"' + val + '"'
                else:
                    val = str(val).replace('.', ',')
                csv += val + ';'
            csv += '\n'

        response = http.HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="export.csv"'
        response.write(csv)
        return response

    def get(self, request, *args, **kwargs):
        if self.request.GET.get('is_csv') == '1':
            return self.csv_view(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['item_url'] = self.item_url
        context['ajax_search_url'] = self.ajax_search_url
        context['search_url'] = self.search_url
        context['type'] = self.invoice_type

        cols = self.request.GET.getlist('cols')
        context['header_values'] = []

        if len(cols):
            for c in cols:
                for ac in lgc_forms.INVOICE_SEARCH_COLS_CHOICES:
                    if ac[0] == c:
                        context['header_values'].append(ac)
        else:
            # set 'cols' in InvoiceSearchform to have these fields selected
            context['header_values'] = [
                ('number', 'ID'), ('with_regard_to', _('Employee Name')),
                ('client_info', _('Company / Client')),
                ('invoice_date', _('Date')),
                ('get_total_items', _('Items')),
                ('total', _('Total (+VAT)')),
            ]

        context['exclude_order_by'] = [
            'get_responsibles', 'person_first_name', 'person_last_name',
            'person_home_entity', 'person_host_entity', 'get_process',
            'entity_info', 'get_client_id', 'client_info',
            'validated', 'to_be_done', 'get_various_expenses',
            'get_various_expenses_vat', 'get_various_expenses_plus_vat',
            'remaining_balance', 'get_total_items', 'get_total_items_vat',
            'get_total_items_plus_vat', 'get_total_disbursements',
            'get_total_disbursements_vat', 'get_total_disbursements_plus_vat',
            'get_total_disbursements_no_various_expenses',
            'get_total_disbursements_plus_vat_no_various_expenses',
            'get_total_plus_vat', 'get_total', 'get_vat', 'validation_date',
        ]
        if self.invoice_type != lgc_models.QUOTATION:
            context['totals'] = []
            if self.eur['items']:
                context['totals'].append(('EUR', self.eur))
            if self.usd['items']:
                context['totals'].append(('USD', self.usd))
            if self.cad['items']:
                context['totals'].append(('CAD', self.cad))
            if self.gbp['items']:
                context['totals'].append(('GBP', self.gbp))

        context['search_form'] = self.get_search_form()
        return pagination(self.request, context, self.this_url)

class QuotationListView(InvoiceListView):
    title = ugettext_lazy('Quotations')
    this_url = reverse_lazy('lgc-quotations')
    search_url = reverse_lazy('lgc-quotations')
    ajax_search_url = reverse_lazy('lgc-quotation-search-ajax')
    objs = lgc_models.Invoice.objects.filter(type=lgc_models.QUOTATION)
    invoice_type = lgc_models.QUOTATION

class CreditNoteListView(InvoiceListView):
    title = ugettext_lazy('Credit Notes')
    this_url = reverse_lazy('lgc-credit-notes')
    search_url = reverse_lazy('lgc-credit-notes')
    ajax_search_url = reverse_lazy('lgc-credit-notes-search-ajax')
    objs = lgc_models.Invoice.objects.filter(type=lgc_models.CREDIT)
    invoice_type = lgc_models.CREDIT

class InvoiceDeleteView(BillingTest, DeleteView):
    model = lgc_models.Invoice
    success_url = reverse_lazy('lgc-invoices')
    title = ugettext_lazy('Delete Invoice')
    cancel_url = 'lgc-invoice'
    obj_name = ugettext_lazy('Invoice')
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
        success_message = (_("Invoice %(name)s successfully deleted."%
                           {'name': name}))
        messages.success(self.request, success_message)
        return super().delete(request, *args, **kwargs)

class InvoiceCommonView(BillingTestLocalUser):
    model = lgc_models.Invoice
    template_name = 'lgc/generic_form_with_formsets.html'
    success_url = 'lgc-invoice'
    fields = '__all__'
    disbursement_receipt_btn_id = 'disbursement_receipt_btn_id'
    form_diff = []
    is_items_diff = False
    is_disbursements_diff = False

    def get_success_url(self):
        return reverse_lazy(self.success_url, kwargs={'pk':self.object.id})

    def get_person_and_process(self):
        if not hasattr(self, 'object') or self.object == None:
            pid = self.request.GET.get('pid')
            proc_id = self.request.GET.get('proc_id')
            person = lgc_models.Person.objects.filter(id=pid).all()
            if len(person) != 1:
                return None, None
            person = person[0]
            proc = lgc_models.PersonProcess.objects.filter(id=proc_id).all()
            if len(proc) != 1:
                return None, None
            proc = proc[0]
            return person, proc

        person = None
        proc = None
        if self.object.person != None:
            person = self.object.person
        if self.object.process != None:
            proc = self.object.process

        return person, proc

    def set_client_info(self, context):
        if not hasattr(self, 'object') or self.object == None:
            return
        obj = self.get_object()
        content = ''
        if obj.first_name + obj.last_name != '':
            content += obj.first_name + ' ' + obj.last_name + '<br>'
        if obj.company != '':
            content += obj.company + '<br>'
        if obj.address != '':
            content += obj.address + '<br>'
        if obj.post_code != '':
            content += obj.post_code + '<br>'
        if obj.city != '':
            content += obj.city + '<br>'
        if obj.country != '':
            content += obj.country.name + '<br>'
        if obj.siret:
            content += 'SIRET: ' + obj.siret + '<br>'

        context['client_info'] = mark_safe(content)

    def get_formsets(self):
        formsets = []
        ItemFormSet = modelformset_factory(lgc_models.InvoiceItem,
                                           form=lgc_forms.InvoiceItemForm,
                                           can_delete=True)
        if not self.object or self.object.type != lgc_models.CREDIT:
            DisbursementFormSet = modelformset_factory(lgc_models.InvoiceDisbursement,
                                                       form=lgc_forms.InvoiceDisbursementForm,
                                                       can_delete=True)

        if self.request.POST:
            formsets.append(ItemFormSet(self.request.POST, prefix='items'))
            if not self.object or self.object.type != lgc_models.CREDIT:
                formsets.append(DisbursementFormSet(self.request.POST,
                                                    prefix='disbursements'))
        else:
            if self.object:
                item_queryset = lgc_models.InvoiceItem.objects.filter(invoice=self.object)
                if self.object.type != lgc_models.CREDIT:
                    disbursement_queryset = lgc_models.InvoiceDisbursement.objects.filter(invoice=self.object)
            else:
                item_queryset = lgc_models.InvoiceItem.objects.none()
                disbursement_queryset = lgc_models.InvoiceDisbursement.objects.none()

            formsets.append(ItemFormSet(queryset=item_queryset, prefix='items'))
            if not self.object or self.object.type != lgc_models.CREDIT:
                formsets.append(DisbursementFormSet(queryset=disbursement_queryset,
                                                    prefix='disbursements'))
        formsets[0].title = _('Items')
        formsets[0].id = 'items_id'
        formsets[0].err_msg = _('Invalid Item table')

        if not self.object or self.object.type != lgc_models.CREDIT:
            formsets[1].title = _('Disbursements')
            formsets[1].id = 'disbursements_id'
            formsets[1].err_msg = _('Invalid Disbursement table')
        return formsets

    def get_doc_forms(self):
        if self.object and self.object.type == lgc_models.CREDIT:
            return None, None

        DocumentFormSet = modelformset_factory(lgc_models.DisbursementDocument,
                                               form=lgc_forms.DisbursementDocumentFormSet,
                                               can_delete=True, extra=0)
        if self.request.POST:
            docs = DocumentFormSet(self.request.POST, self.request.FILES,
                                   prefix='docs')
            doc = lgc_forms.DisbursementDocumentForm(self.request.POST, self.request.FILES)
        else:
            docs = DocumentFormSet(prefix='docs', queryset=lgc_models.DisbursementDocument.objects.filter(invoice=self.object))
            doc = lgc_forms.DisbursementDocumentForm()
        return doc, docs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person, process = self.get_person_and_process()
        pcv = lgc_views.PersonCommonView()

        if person:
            context['form'].fields['with_regard_to'].initial = (
                person.first_name + ' ' + person.last_name
            )
        context['title'] = self.title

        if self.object and self.object.id:
            context['title'] += ' ID ' + str(self.object.number)

        context['person'] = person
        context['person_process'] = process

        self.set_client_info(context)
        context['formsets'] = self.get_formsets()
        context['doc'], context['docs'] = self.get_doc_forms()
        context['button_collapse_id'] = self.disbursement_receipt_btn_id
        context['button_label'] = _('Disbursement receipts')
        context['doc_download_url'] = 'lgc-receipt-download'

        context['form_diff'] = self.form_diff
        context['formsets_diff'] = []
        if self.is_items_diff:
            context['formsets_diff'] += [('items', _('Items'),
                                          pcv.get_formset_objs(lgc_models.InvoiceItem.objects.filter(invoice=self.object)))]
        if self.is_disbursements_diff:
            context['formsets_diff'] += [('disbursements', _('Disbursements'),
                                          pcv.get_formset_objs(lgc_models.InvoiceDisbursement.objects.filter(invoice=self.object)))]

        if self.form_diff or len(context['formsets_diff']):
            changes_form = lgc_forms.ChangesDetectedForm()
            changes_form.helper = FormHelper()
            changes_form.helper.form_tag = False
            context['changes_detected_form'] = changes_form

        return context

    def check_formsets_diff(self, pcv, formsets):
        for formset in formsets:
            if formset.id == 'items_id':
                self.is_items_diff = pcv.have_objs_changed(formset,
                                                           lgc_models.InvoiceItem.objects.filter(invoice=self.object))
            elif formset.id == 'disbursements_id':
                self.is_disbursements_diff = pcv.have_objs_changed(formset,
                                                                   lgc_models.InvoiceDisbursement.objects.filter(invoice=self.object))
        return self.is_items_diff or self.is_disbursements_diff

    def check_form_diff(self, pcv, obj, form, formsets):
        if obj == None:
            return []

        if form.cleaned_data['version'] == obj.version:
            return False

        if not form.cleaned_data['client_update']:
            ignore_list = ['first_name', 'last_name', 'company', 'email',
                           'phone_number', 'cell_phone_number', 'siret',
                           'vat', 'address', 'post_code', 'city', 'country',
                           'with_regard_to']
        else:
            ignore_list = []

        self.form_diff = pcv.check_form_diff2(obj, form, form.cleaned_data,
                                              ignore_list)
        formsets_diff = self.check_formsets_diff(pcv, formsets)
        return len(self.form_diff) or formsets_diff

    def set_client_billing_addr(self, client, invoice):
            invoice.company = client.get_company
            invoice.address = client.get_address
            invoice.post_code = client.get_post_code
            invoice.city = client.get_city
            invoice.country = client.get_country

    def form_valid(self, form):
        if self.object:
            invoice = self.get_object()
            if invoice.state == lgc_models.INVOICE_STATE_PAID:
                messages.error(self.request,
                               _('Cannot update a validated invoice.'));
                return super().form_invalid(form)
        else:
            invoice = None

        pcv = lgc_views.PersonCommonView()
        formsets = self.get_formsets()

        person, person_process = self.get_person_and_process()
        form.instance.person = person
        form.instance.last_modified_date = timezone.now()

        if self.request.GET.get('quote') == '1':
            form.instance.type = lgc_models.QUOTATION

        if (invoice == None and
            len(person_process.invoice_set.filter(type=form.instance.type))):
            messages.error(self.request,
                           _('There is already an invoice/quote for this process'))
            return self.form_invalid(form)

        if person_process and person_process.process:
            form.instance.process = person_process

        err_msg = _('Client not set.')

        if not form.cleaned_data['client_update']:
            if self.object == None:
                messages.error(self.request, err_msg)
                return super().form_invalid(form)
            dummy_client = lgc_models.Client()
            pcv.copy_related_object(invoice, form.instance, dummy_client)
        elif form.cleaned_data['client']:
            client = form.cleaned_data['client']
            pcv.copy_related_object(client, form.instance, client)
            self.set_client_billing_addr(client, form.instance)

        if person and invoice == None:
            form.instance.with_regard_to = (
                person.first_name + ' ' + person.last_name
            )

        if self.object:
            self.object = self.get_object()
            changes_action = self.request.POST.get('changes_action', '')
            if changes_action == lgc_forms.CHANGES_DETECTED_DISCARD:
                return redirect(self.get_success_url())

            if not pcv.are_formsets_valid(self, formsets):
                return super().form_invalid(form)

            if changes_action != lgc_forms.CHANGES_DETECTED_FORCE:
                if self.check_form_diff(pcv, self.object, form, formsets):
                    return super().form_invalid(form)

            form.instance.version = self.object.version + 1
        else:
            if not pcv.are_formsets_valid(self, formsets):
                return super().form_invalid(form)
            changes_action = None

        form.instance.modified_by = self.request.user
        form.instance.last_modified_date = timezone.now()

        for formset in formsets:
            if not formset.is_valid():
                messages.error(self.request, formset.err_msg)
                return super().form_invalid(form)
        if self.object and self.object.type == lgc_models.INVOICE:
            doc, deleted_docs = self.get_doc_forms()
            docs = lgc_models.DisbursementDocument.objects.filter(invoice=self.object)

            if lgc_views.check_docs(self, doc, docs) < 0:
                return super().form_invalid(form)
        else:
            doc = None
            deleted_docs = None

        with transaction.atomic():
            self.object = form.save()

            for formset in formsets:
                for obj in formset.deleted_forms:
                    if (obj.instance.id != None and
                        obj.instance.invoice == self.object):
                        obj.instance.delete()

                instances = formset.save(commit=False)
                for i in instances:
                    if ((i.invoice_id and i.invoice_id != self.object.id) or
                        not i.description):
                        continue
                    i.invoice = self.object
                    i.save()
            log.debug('total: %d items: %d items_vat: %d disbursements: %d disbursements_vat:%d'%(
                form.instance.get_total, form.instance.get_total_items,
                form.instance.get_total_items_vat,
                form.instance.get_total_disbursements,
                form.instance.get_total_disbursements_vat))

            total = form.instance.get_total_plus_vat
            if total != float(form.instance.total):
                log.error('invoice %d total does not match. Computed total: %f form total: %f',
                          form.instance.id, total, float(form.instance.total))
                messages.error(self.request,
                               _('Total does not match. Contact your administrator'))

            if deleted_docs:
                for d in deleted_docs.deleted_forms:
                    if d.instance.id == None:
                        continue
                    os.remove(os.path.join(settings.MEDIA_ROOT,
                                           d.instance.document.name))
                    d.instance.delete()

                if doc.cleaned_data['document'] != None:
                    doc.instance = lgc_models.DisbursementDocument()
                    doc.instance.document = doc.cleaned_data['document']
                    doc.instance.description = doc.cleaned_data['description']
                    doc.instance.invoice = self.object
                    doc.save()

            if form.instance.type == lgc_models.CREDIT:
                self.success_message = self.credit_note_success_message
            elif form.instance.type == lgc_models.QUOTATION:
                self.success_message = self.quote_success_message
            elif person_process:
                person_process.invoice_alert = False
                person_process.save()
            messages.success(self.request, self.success_message)
            return http.HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_form(self, form_class=lgc_forms.InvoiceCreateForm):
        if self.object:
            if self.object.type == lgc_models.INVOICE:
                form = super().get_form(form_class=form_class)
            else:
                form = super().get_form(form_class=lgc_forms.QuotationUpdateForm)
        else:
            if self.request.GET.get('quote') == '1':
                form = super().get_form(form_class=lgc_forms.QuotationCreateForm)
            else:
                form = super().get_form(form_class=form_class)
        form.helper = FormHelper()
        form.helper.form_tag = False
        gen_invoice_html = None
        gen_credit_note_html = None
        gen_pdf_html = None
        state_div = None

        if self.object:
            state_div = Div('state', css_class='form-group col-md-2')
            if (self.object.type == lgc_models.QUOTATION and self.object.process and
                self.object.process.get_invoice == None):
                gen_invoice_html = HTML(('&nbsp;<a href="' +
                                         str(reverse_lazy('lgc-gen-invoice',
                                                          kwargs={'pk':self.object.id})) +
                                         '" class="btn btn-outline-info">' +
                                         _('Create invoice') + '</a>'))
            elif (self.object.type == lgc_models.INVOICE and
                  (self.object.state == lgc_models.INVOICE_STATE_PAID or
                   self.object.state == lgc_models.INVOICE_STATE_DONE) and
                  self.object.process and
                  self.object.process.get_credit_note == None):
                gen_credit_note_html = HTML(('&nbsp;<a href="' +
                                             str(reverse_lazy('lgc-gen-credit-note',
                                                              kwargs={'pk':self.object.id})) +
                                             '" class="btn btn-outline-info">' +
                                             _('Create Credit Note') + '</a>'))
            if self.request.user.billing:
                gen_pdf_html = HTML(('&nbsp;<a href="' +
                                     str(reverse_lazy('lgc-billing-pdf',
                                                      kwargs={'pk':self.object.id})) +
                                     '" class="btn btn-outline-info">PDF</a>'))
        layout = Layout(
            Div('version'), Div('client_update'), Div('client'), Div('total'),
            HTML(get_template(CURRENT_DIR, 'lgc/billing_template.html')),
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
                css_class='collapse show', id='collapsePO'),
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
                state_div,
                css_class='form-row')
        )
        if self.object and self.object.type == lgc_models.INVOICE:
            layout.append(
                Div(
                    Div('already_paid',
                        css_class='form-group col-md-2 border-left border-top border-bottom'),
                    Div('already_paid_desc',
                        css_class='form-group col-md-2 border-right border-top border-bottom'),
                    css_class='form-row')
            )
        layout.append(Div(
            Div('invoice_description', css_class='form-group col-md-4'),
            Div(HTML('&nbsp;'), css_class='form-group col-md-2'),
            css_class='form-row'),
        )
        layout.append(Div(
            Div(HTML(get_template(CURRENT_DIR,
                                  'lgc/billing_formsets_template.html')),
                css_class='form-group col-md-9'),
            css_class='form-row')
        )
        if self.object and self.object.type == lgc_models.INVOICE:
            layout.append(Div(
                Div(HTML(get_template(CURRENT_DIR, 'lgc/button_collapse.html') + '<hr>'),
                    css_class='form-group col-md-9'),
                css_class='form-row')
            )
            layout.append(Div(
                Div(HTML(get_template(CURRENT_DIR, 'lgc/document_form.html')),
                    HTML('<hr>'),
                    css_class='form-group col-md-9 collapse',
                    id=self.disbursement_receipt_btn_id),
                css_class='form-row')
            )
        layout.append(
            HTML(get_template(CURRENT_DIR, 'lgc/billing_total_template.html')),
        )

        action_url = None
        if self.object:
            layout.append(Div('number'))
            if self.object.state == lgc_models.INVOICE_STATE_PAID:
                action_url = str(reverse_lazy('lgc-invoices'))
                action = _('Invoice list')
            else:
                action = _('Update')
        else:
            action = _('Create')
        if action_url == None:
            layout.append(HTML('<button class="btn btn-outline-info" type="submit" ' +
                               'onclick="return invoice_form_checks(\'' +
                               _('If the state PAID is set, the invoice will not be editable anymore.').replace("'", "\\'") +
                               '\');">' + action + '</button>'))
        else:
            layout.append(HTML('<a href="' + action_url +
                               '" class="btn btn-outline-info">' +
                               action + '</a>'))
        layout.append(gen_invoice_html)
        layout.append(gen_pdf_html)
        layout.append(gen_credit_note_html);
        form.helper.layout = layout
        return form

class InvoiceCreateView(InvoiceCommonView, SuccessMessageMixin, CreateView):
    title = ugettext_lazy('New Invoice')
    success_message = ugettext_lazy('Invoice successfully created.')
    quote_success_message = ugettext_lazy('Quotation successfully created.')

    def get_context_data(self, **kwargs):
        if self.request.GET.get('quote') == '1':
            self.title = _('New Quotation')
            self.success_message = self.quote_success_message
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        if self.request.GET.get('quote') == '1':
            objs = lgc_models.Invoice.objects.filter(type=lgc_models.QUOTATION)
            self.success_message = self.quote_success_message
        else:
            objs = lgc_models.Invoice.objects.filter(type=lgc_models.INVOICE)
        max_number = objs.all().aggregate(Max('number'))
        if max_number['number__max'] == None:
            invoice_number = 1
        else:
            invoice_number = max_number['number__max'] + 1
        form.instance.number = invoice_number

        return super().form_valid(form)

class InvoiceUpdateView(InvoiceCommonView, SuccessMessageMixin, UpdateView):
    title = ugettext_lazy('Invoice')
    success_message = ugettext_lazy('Invoice successfully updated.')
    quote_success_message = ugettext_lazy('Quotation successfully updated.')
    credit_note_success_message = ugettext_lazy('Credit note successfully updated.')

    def test_func(self):
        if not super().test_func():
            return False
        if self.request.user.billing or self.request.user.is_staff:
            return True

        self.object = self.get_object()
        if (self.object.state == lgc_models.INVOICE_STATE_PAID or
            self.object.state == lgc_models.INVOICE_STATE_DONE):
            return self.request.user in self.object.person.responsible.all()
        return True

    def get_context_data(self, **kwargs):
        if self.object.type == lgc_models.QUOTATION:
            self.title = _('Update quotation')
        elif self.object.type == lgc_models.CREDIT:
            self.title = _('Update credit note')
        return super().get_context_data(**kwargs)

    def get_form(self, form_class=lgc_forms.InvoiceUpdateForm):
        return super().get_form(form_class=form_class)

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

    col_list = ['first_name', 'last_name', 'company']
    col_list = set_bold_search_attrs(objs, col_list, term)
    objs = objs[:10]

    context = {
        'objects': objs,
        'col_list': col_list,
    }
    return render(request, 'lgc/generic_search.html', context)

def ajax_invoice_common_search_view(request, objs):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()
    if not request.user.billing:
        return http.HttpResponseForbidden()

    term = request.GET.get('term', '')
    term_int = None

    objs = (objs.filter(person__first_name__istartswith=term)|
            objs.filter(person__last_name__istartswith=term)|
            objs.filter(person__home_entity__istartswith=term)|
            objs.filter(person__host_entity__istartswith=term)|
            objs.filter(first_name__istartswith=term)|
            objs.filter(last_name__istartswith=term)|
            objs.filter(company__istartswith=term))

    try:
        term_int = int(term)
        objs = lgc_models.Invoice.objects.filter(number__istartswith=term_int)
    except:
        pass

    col_list = ['person_first_name', 'person_last_name', 'person_home_entity',
                'person_host_entity', 'company', 'first_name',
                'last_name', 'number']
    col_list = set_bold_search_attrs(objs, col_list, term, term_int)
    objs = objs[:10]

    context = {
        'objects': objs,
        'col_list': col_list,
    }
    return render(request, 'lgc/generic_search.html', context)

@login_required
def ajax_quotation_search_view(request):
    objs = lgc_models.Invoice.objects.filter(type=lgc_models.QUOTATION)
    return ajax_invoice_common_search_view(request, objs)

@login_required
def ajax_credit_notes_search_view(request):
    objs = lgc_models.Invoice.objects.filter(type=lgc_models.CREDIT)
    return ajax_invoice_common_search_view(request, objs)

@login_required
def ajax_invoice_search_view(request):
    objs = lgc_models.Invoice.objects.filter(type=lgc_models.INVOICE)
    return ajax_invoice_common_search_view(request, objs)

@login_required
def invoice_insert_client(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    context = {
        'title': _('Insert Client'),
        'object_list': lgc_models.Client.objects.all(),
    }
    return render(request, 'lgc/insert_client.html', context)

def get_url_params(request):
    index = request.GET.get('index')
    currency = request.GET.get('currency')
    if index and currency:
        return '?index=' + index + '&currency=' + currency
    return ''

class InvoiceItemCommonView(BillingTestLocalUser):
    model = lgc_models.Item
    template_name ='lgc/insert_invoice_item.html'
    success_url = 'lgc-insert-item'
    edit_expanded = False
    delete_url = 'lgc-delete-item'
    update_url = 'lgc-update-item'

    def get_success_url(self):
        url = reverse_lazy(self.success_url)
        params = get_url_params(self.request)
        return url + params

    def form_valid(self, form):
        if self.model == lgc_models.Client:
            return super().form_valid(form)

        if self.object:
            _str = _('Item %(item)s successfully updated.'%
                     {'item':form.instance.title})
        else:
            _str = _('Item %(item)s successfully created.'%
                     {'item':form.instance.title})
        messages.success(self.request, _str)
        return super().form_valid(form)

    def form_invalid(self, form):
        self.edit_expanded = True
        form = self.get_form()
        return super().form_invalid(form)

    def get_form(self, form_class=lgc_forms.ClientCreateForm):
        if self.model == lgc_models.Item:
            form_class = lgc_forms.ItemForm
        elif self.model == lgc_models.Disbursement:
            form_class = lgc_forms.DisbursementForm
        elif self.model == lgc_models.Client:
            return super().get_form(form_class=lgc_forms.ClientCreateForm)
        else:
            raise Http404
        title = _('Edit item')
        form = super().get_form(form_class=form_class)
        form.helper = FormHelper()
        if self.object == None:
            action = _('Add')
        else:
            action = _('Update')
            title += ' Id: ' + str(self.object.id)

        if self.edit_expanded:
            body_class = "collapse show"
            aria_expanded = "true"
        else:
            body_class = "collapse"
            aria_expanded = "false"

        if self.model == lgc_models.Item:
            rate_div = Div(Div('rate_EUR', css_class='form-group col-md-1'),
                           Div('rate_USD', css_class='form-group col-md-1'),
                           Div('rate_CAD', css_class='form-group col-md-1'),
                           Div('rate_GBP', css_class='form-group col-md-1'),
                           css_class='form-row')
        else:
            rate_div = Div(Div('rate', css_class='form-group col-md-1'),
                           Div('currency', css_class='form-group col-md-1'),
                           css_class='form-row')

        form.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML('<button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapse_item" aria-expanded="' + aria_expanded + '" aria-controls="collapse_item">' + title + '</button>'),
                        css_class='card-header', id='heading_item'),
                    Div(
                        Div(
                            Div(Div('title', css_class='form-group col-md-1'),
                                css_class='form-row'),
                            Div(Div('description', css_class='form-group col-md-2'),
                                css_class='form-row'),
                            rate_div,
                            Div(Div(HTML('<button class="btn btn-outline-info" type="submit">' + action + '</button>'),
                                    css_class="form-group col-md-1"),
                                css_class="form-row"),
                            css_class='card-body'),
                        css_class=body_class, id='collapse_item', arialabelledby='heading_item', dataparent='#item_accordion'),
                    css_class='card', style='overflow:visible;'),
                css_class="accordion", id="item_accordion"
            ),
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['object_list'] = self.model.objects.all()
        context['update_url'] = self.update_url
        context['delete_url'] = self.delete_url

        currency = self.request.GET.get('currency', 'EUR')
        if self.model == lgc_models.Disbursement:
            context['type'] = 'disbursement'
            if lgc_models.Settings.objects.count() == 0:
                settings = lgc_models.Settings()
                settings.rate_EUR = 1
                settings.save()

            context['settings'] = lgc_models.Settings.objects.all()[0]
            return context

        lgc_models.Item.set_currency(currency)
        context['type'] = 'item'
        return context

class InvoiceItemCreateView(InvoiceItemCommonView, CreateView):
    title = ugettext_lazy('Insert Item')

class InvoiceItemUpdateView(InvoiceItemCommonView, UpdateView):
    title = ugettext_lazy('Update Item')
    edit_expanded = True

class InvoiceClientCommonView(InvoiceItemCommonView):
    model = lgc_models.Client
    template_name = 'lgc/insert_client.html'
    delete_url = 'lgc-delete-client'
    update_url = 'lgc-update-client'
    success_url = 'lgc-insert-client'

    def form_valid(self, form):
        if self.object:
            _str = _('Client successfully updated.')
        else:
            _str = _('Client successfully created.')
        messages.success(self.request, _str)
        return super().form_valid(form)

    def get_form(self):
        form_class = lgc_forms.ClientCreateForm
        title = _('Edit Client')
        form = super().get_form(form_class=form_class)
        form.helper = FormHelper()
        if self.object == None:
            action = _('Add')
        else:
            action = _('Update')
            title += ' Id: ' + str(self.object.id)

        if self.edit_expanded:
            body_class = "collapse show"
            aria_expanded = "true"
        else:
            body_class = "collapse"
            aria_expanded = "false"

        form.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML('<button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapse_item" aria-expanded="' + aria_expanded + '" aria-controls="collapse_item">' + title + '</button>'),
                        css_class='card-header', id='heading_item'),
                    Div(
                        Div(
                            Div(Div('first_name', css_class='form-group col-md-2'),
                                Div('last_name', css_class='form-group col-md-2'),
                                Div('company', css_class='form-group col-md-2'),
                                Div('email', css_class='form-group col-md-2'),
                                css_class='form-row'),
                            Div(Div('phone_number', css_class='form-group col-md-2'),
                                Div('cell_phone_number', css_class='form-group col-md-2'),
                                Div('siret', css_class='form-group col-md-2'),
                                Div('vat', css_class='form-group col-md-2'),
                                css_class='form-row'),
                            Div(Div('address', css_class='form-group col-md-2'),
                                Div('post_code', css_class='form-group col-md-2'),
                                Div('city', css_class='form-group col-md-2'),
                                Div('country', css_class='form-group col-md-2'),
                                css_class='form-row'),
                            Div(Div(HTML('<hr><h5>'+ _('Billing Address') +'</h5>'),
                                    css_class='form-group col-md-8'),
                                css_class='form-row'),
                            Div(Div('billing_address', css_class='form-group col-md-2'),
                                Div('billing_post_code', css_class='form-group col-md-2'),
                                Div('billing_city', css_class='form-group col-md-2'),
                                Div('billing_country', css_class='form-group col-md-2'),
                                css_class='form-row'),
                            Div(Div(HTML('<button class="btn btn-outline-info" type="submit">' + action + '</button>'),
                                    css_class="form-group col-md-1"),
                                css_class="form-row"),
                            css_class='card-body'),
                        css_class=body_class, id='collapse_item', arialabelledby='heading_item', dataparent='#item_accordion'),
                    css_class='card', style='overflow:visible;'),
                css_class="accordion", id="item_accordion"
            ),
        )
        return form

class InvoiceClientCreateView(InvoiceClientCommonView, CreateView):
    title = ugettext_lazy('Insert Client')

class InvoiceClientUpdateView(InvoiceClientCommonView, UpdateView):
    title = ugettext_lazy('Update Client')
    edit_expanded = True

class InvoiceDisbursementCommon():
    model = lgc_models.Disbursement
    delete_url = 'lgc-delete-disbursement'
    update_url = 'lgc-update-disbursement'
    success_url = 'lgc-insert-disbursement'

class InvoiceDisbursementCreateView(InvoiceDisbursementCommon,
                                    InvoiceItemCommonView, CreateView):
    title = ugettext_lazy('Insert Disbursement')

class InvoiceDisbursementUpdateView(InvoiceDisbursementCommon,
                                    InvoiceItemUpdateView):
    title = ugettext_lazy('Update Disbursement')


def user_billing_check(request):
    return (request.user.role in user_models.get_internal_roles() and
            request.user.billing)

@login_required
def __invoice_item_delete_view(request, model, url, pk=None):
    if not user_billing_check:
        return http.HttpResponseForbidden()

    if not pk:
        return redirect(url)
    obj = model.objects.filter(id=pk)
    if len(obj) != 1:
        return redirect(url)
    obj = obj[0]
    obj.delete()
    params = get_url_params(request)
    if model == lgc_models.Client:
        messages.success(request, _('Client successfully deleted.'))
    else:
        messages.success(request, _('Item %(item)s successfully deleted.'%
                                    {'item':obj.title}))
    return redirect(url + params)

def invoice_item_delete_view(request, pk=None):
    url = reverse_lazy('lgc-insert-item')
    return __invoice_item_delete_view(request, lgc_models.Item, url, pk)

def invoice_disbursement_delete_view(request, pk=None):
    url = reverse_lazy('lgc-insert-disbursement')
    return __invoice_item_delete_view(request, lgc_models.Disbursement, url, pk)

def invoice_client_delete_view(request, pk=None):
    url = reverse_lazy('lgc-insert-client')
    return __invoice_item_delete_view(request, lgc_models.Client, url, pk)

@login_required
def generate_invoice_from_quote(request, pk):
    if not user_billing_check:
        return http.HttpResponseForbidden()

    invoice_objs = lgc_models.Invoice.objects.filter(type=lgc_models.INVOICE)
    quote = lgc_models.Invoice.objects.filter(type=lgc_models.QUOTATION).filter(id=pk)
    if len(quote) != 1:
        raise Http404
    quote = quote[0]
    if len(quote.process.invoice_set.filter(type=lgc_models.INVOICE)):
        messages.error(request, _('There is already an invoice for this quotation'))
        return redirect('lgc-invoice', quote.id)

    max_number = invoice_objs.all().aggregate(Max('number'))
    if max_number['number__max'] == None:
        max_number = 1
    else:
        max_number = max_number['number__max'] + 1

    quote.id = None
    quote.number = max_number
    quote.type = lgc_models.INVOICE
    quote.save()

    for items in [lgc_models.InvoiceItem.objects.filter(invoice=pk),
                  lgc_models.InvoiceDisbursement.objects.filter(invoice=pk)]:
        if len(items) == 0:
            continue
        for item in items.all():
            item.id = None
            item.invoice = quote
            item.save()

    messages.success(request, _('Invoice %(id)d has been successfully created.')%
                     {'id':quote.number})
    return redirect('lgc-invoice', quote.id)

@login_required
def generate_credit_note_from_invoice(request, pk):
    if not user_billing_check:
        return http.HttpResponseForbidden()

    credit_notes_objs = lgc_models.Invoice.objects.filter(type=lgc_models.CREDIT)
    invoice = lgc_models.Invoice.objects.filter(type=lgc_models.INVOICE).filter(id=pk)
    if len(invoice) != 1:
        raise Http404

    invoice = invoice[0]
    if len(invoice.process.invoice_set.filter(type=lgc_models.CREDIT)):
        messages.error(request, _('There is already a credit note for this invoice'))
        return redirect('lgc-invoice', invoice.id)

    max_number = credit_notes_objs.all().aggregate(Max('number'))
    if max_number['number__max'] == None:
        max_number = 1
    else:
        max_number = max_number['number__max'] + 1

    invoice.id = None
    invoice.number = max_number
    invoice.type = lgc_models.CREDIT
    invoice.state = lgc_models.INVOICE_STATE_PENDING
    invoice.already_paid = 0
    invoice.various_expenses = False
    invoice.total = 0
    invoice.save()

    messages.success(request, _('Credit Note %(id)d has been successfully created.')%
                     {'id':invoice.number})
    return redirect('lgc-invoice', invoice.id)

@login_required
def billing_pdf_view(request, pk):
    if not request.user.billing:
        return http.HttpResponseForbidden()

    invoice = lgc_models.Invoice.objects.filter(id=pk)
    if len(invoice) != 1:
        raise Http404
    invoice = invoice[0]

    response = http.HttpResponse(content_type='application/pdf')
    if invoice.type == lgc_models.QUOTATION:
        filename = 'DE'
    elif invoice.type == lgc_models.CREDIT:
        filename = 'AV'
    else:
        filename = 'FA'
    filename += str(invoice.number).zfill(5) + '.pdf'
    response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
    pdf = subprocess.Popen(os.path.join(settings.BASE_DIR, 'php_pdf/print.php') +
                           ' ' + str(invoice.id),
                           shell=True, stdout=subprocess.PIPE).stdout.read()
    response.write(pdf)
    return response

@login_required
def download_receipt_file(request, *args, **kwargs):
    pk = kwargs.get('pk', '')
    doc = lgc_models.DisbursementDocument.objects.filter(id=pk).all()
    if doc == None or len(doc) != 1:
        raise Http404

    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    file_path = os.path.join(settings.MEDIA_ROOT, doc[0].document.name)
    if not os.path.exists(file_path):
        raise Http404
    with open(file_path, 'rb') as fh:
        res = http.HttpResponse(fh.read(), content_type='application/octet-stream')
        res['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
        return res
    raise Http404

class InvoiceReminderListView(BillingTest, ListView):
    template_name = 'lgc/sub_generic_list.html'
    model = lgc_models.InvoiceReminder
    title = ugettext_lazy('Invoice Reminders')
    create_url = reverse_lazy('lgc-billing-reminder-create')
    item_url = 'lgc-billing-reminder'
    this_url = reverse_lazy('lgc-billing-reminders')
    search_url = reverse_lazy('lgc-billing-reminders')

    def test_func(self):
        return self.request.user.billing

    def get_ordering(self):
        return self.request.GET.get('order_by', 'id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['create_url'] = self.create_url
        context['item_url'] = self.item_url
        context['header_values'] = [
            ('id', 'ID'), ('name', _('Name')), ('number_of_days', _('Days')),
            ('enabled', _('Enabled')),
        ]
        return pagination(self.request, context, self.this_url)

    def get_queryset(self):
        term = self.request.GET.get('term')
        order_by = self.get_ordering()

        if not term:
            return self.model.objects.order_by(order_by)
        objs = lgc_models.InvoiceReminder.objects.filter(name__istartswith=term)
        return objs.order_by(order_by)

class InvoiceReminderCreateView(BillingTest, SuccessMessageMixin, CreateView):
    model = lgc_models.InvoiceReminder
    success_message = ugettext_lazy('Invoice Reminder successfully created')
    template_name = 'lgc/generic_form.html'
    success_url = reverse_lazy('lgc-billing-reminder-create')
    title = ugettext_lazy('New Invoice Reminder')
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def test_func(self):
        return self.request.user.billing

    def get_form(self, form_class=lgc_forms.InvoiceReminderForm):
        return super().get_form(form_class=form_class)

class InvoiceReminderUpdateView(BillingTest, SuccessMessageMixin, UpdateView):
    model = lgc_models.InvoiceReminder
    success_message = ugettext_lazy('Invoice Reminder successfully updated')
    success_url = 'lgc-billing-reminder'
    template_name = 'lgc/generic_form.html'
    title = ugettext_lazy('Invoice Reminder')
    delete_url = 'lgc-billing-reminder-delete'
    fields = '__all__'

    def get_success_url(self):
        self.object = self.get_object()
        return reverse_lazy(self.success_url, kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['delete_url'] = reverse_lazy(self.delete_url,
                                             kwargs={'pk':self.object.id})
        return context

    def test_func(self):
        return self.request.user.billing

    def get_form(self, form_class=lgc_forms.InvoiceReminderForm):
        return super().get_form(form_class=form_class)

class InvoiceReminderDeleteView(BillingTest, DeleteView):
    model = lgc_models.InvoiceReminder
    template_name = 'lgc/process_confirm_delete.html'
    success_message = ugettext_lazy('Invoice Reminder successfully deleted')
    success_url = reverse_lazy('lgc-billing-reminders')
    title = ugettext_lazy('Delete Invoice Reminder')
    cancel_url = 'lgc-billing-reminder'
    obj_name = ugettext_lazy('Invoice Reminder')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['cancel_url'] = reverse_lazy(self.cancel_url,
                                             kwargs={'pk':self.object.id})
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, args, kwargs)

    def test_func(self):
        return self.request.user.billing
