import pdb                # pdb.set_trace()
from django.db import transaction
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from common.utils import (pagination, lgc_send_email, must_be_staff,
                          set_bold_search_attrs, get_template)
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
from django.db.models import Max
from common import lgc_types
import string
import random
import datetime
import os
CURRENT_DIR = Path(__file__).parent

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

class InvoiceListView(BillingTest, ListView):
    template_name = 'lgc/sub_generic_list.html'
    model = lgc_models.Invoice
    title = _('Invoices')
    item_url = 'lgc-invoice'
    this_url = reverse_lazy('lgc-invoices')
    ajax_search_url = reverse_lazy('lgc-invoice-search-ajax')
    search_url = reverse_lazy('lgc-invoices')

    def get_queryset(self):
        objs = self.model.objects.filter(type=lgc_models.INVOICE)
        term = self.request.GET.get('term', '')
        order_by = self.get_ordering()

        if term == '':
            return objs.order_by(order_by)
        objs = (objs.filter(email__istartswith=term)|
                objs.filter(first_name__istartswith=term)|
                objs.filter(last_name__istartswith=term)|
                objs.filter(company__istartswith=term))
        try:
            term_int = int(term)
            objs = lgc_models.Invoice.objects.filter(number__istartswith=term_int)
        except:
            pass

        return objs.order_by(order_by)

    def get_ordering(self):
        return self.request.GET.get('order_by', 'id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['item_url'] = self.item_url
        context['ajax_search_url'] = self.ajax_search_url
        context['search_url'] = self.search_url
        context['header_values'] = [
            ('ID', 'number'), (_('First Name'), 'first_name'),
            (_('First Name'), 'first_name'), (_('Company'), 'company'),
            ('Email', 'email'), (_('Date'), 'invoice_date'),
        ]
        return pagination(self.request, context, self.this_url)

class QuotationListView(InvoiceListView):
    title = _('Quotations')
    this_url = reverse_lazy('lgc-quotations')
    search_url = reverse_lazy('lgc-quotations')

    def get_queryset(self):
        objs = self.model.objects.filter(type=lgc_models.QUOTATION)
        term = self.request.GET.get('term', '')
        order_by = self.get_ordering()

        if term == '':
            return objs.order_by(order_by)
        objs = (objs.filter(email__istartswith=term)|
                objs.filter(first_name__istartswith=term)|
                objs.filter(last_name__istartswith=term)|
                objs.filter(company__istartswith=term))
        try:
            term_int = int(term)
            objs = lgc_models.Invoice.objects.filter(number__istartswith=term_int)
        except:
            pass

        return objs.order_by(order_by)

class InvoiceDeleteView(BillingTest, DeleteView):
    model = lgc_models.Invoice
    success_url = reverse_lazy('lgc-invoices')
    title = _('Delete Invoice')
    cancel_url = 'lgc-invoice'
    obj_name = _('Invoice')
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

class InvoiceCommonView(BillingTest):
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
        if self.object.person != None and self.object.process != None:
            person = self.object.person
            proc = self.object.process
            return person, proc

        return None, None

    def set_client_info(self, context):
        if not hasattr(self, 'object') or self.object == None:
            return
        content = ''
        if self.object.first_name + self.object.last_name != '':
            content += self.object.first_name + ' ' + self.object.last_name + '<br>'
        if self.object.company != '':
            content += self.object.company + '<br>'
        if self.object.address != '':
            content += self.object.address + '<br>'
        if self.object.post_code != '':
            content += self.object.post_code + '<br>'
        if self.object.city != '':
            content += self.object.city + '<br>'
        if self.object.country != '':
            content += self.object.country.name + '<br>'
        if self.object.siret:
            content += 'SIRET: ' + self.object.siret + '<br>'

        context['client_info'] = mark_safe(content)

    def get_formsets(self):
        formsets = []
        ItemFormSet = modelformset_factory(lgc_models.InvoiceItem,
                                           form=lgc_forms.InvoiceItemForm,
                                           can_delete=True)
        DisbursementFormSet = modelformset_factory(lgc_models.InvoiceDisbursement,
                                                   form=lgc_forms.InvoiceDisbursementForm,
                                                   can_delete=True)

        if self.request.POST:
            formsets.append(ItemFormSet(self.request.POST, prefix='items'))
            formsets.append(DisbursementFormSet(self.request.POST, prefix='disbursements'))
        else:
            if self.object:
                item_queryset = lgc_models.InvoiceItem.objects.filter(invoice=self.object)
                disbursement_queryset = lgc_models.InvoiceDisbursement.objects.filter(invoice=self.object)
            else:
                item_queryset = lgc_models.InvoiceItem.objects.none()
                disbursement_queryset = lgc_models.InvoiceDisbursement.objects.none()

            formsets.append(ItemFormSet(queryset=item_queryset, prefix='items'))
            formsets.append(DisbursementFormSet(queryset=disbursement_queryset,
                                                prefix='disbursements'))
        formsets[0].title = _('Items')
        formsets[0].id = 'items_id'
        formsets[0].err_msg = _('Invalid Item table')

        formsets[1].title = _('Disbursements')
        formsets[1].id = 'disbursements_id'
        formsets[1].err_msg = _('Invalid Disbursement table')
        return formsets

    def get_doc_forms(self):
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

        self.form_diff = pcv.check_form_diff2(obj, form, form.cleaned_data, ignore_list)
        formsets_diff = self.check_formsets_diff(pcv, formsets)
        return len(self.form_diff) or formsets_diff

    def form_valid(self, form):
        pcv = lgc_views.PersonCommonView()
        formsets = self.get_formsets()

        invoice = None
        person, person_process = self.get_person_and_process()
        form.instance.person = person

        if self.request.GET.get('quote') == '1':
            form.instance.type = lgc_models.QUOTATION

        if person_process and person_process.process:
            form.instance.process = person_process

        if form.instance.id:
            obj = lgc_models.Invoice.objects.filter(id=form.instance.id)
            if len(obj) != 1 and self.object:
                messages.error(self.request, err_msg)
                return super().form_invalid(form)
            if len(obj) == 1:
                invoice = obj[0]

        err_msg = _('Client not set.')

        if not form.cleaned_data['client_update']:
            if self.object == None:
                messages.error(self.request, err_msg)
                return super().form_invalid(form)
            dummy_client = lgc_models.Client()
            pcv.copy_related_object(invoice, form.instance, dummy_client)
        elif form.cleaned_data['client_update'] and form.cleaned_data['client']:
            client = form.cleaned_data['client']
            pcv.copy_related_object(client, form.instance, client)

        if invoice:
            form.instance.with_regard_to = invoice.with_regard_to
        elif person:
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
        form.instance.modification_date = timezone.now()


        for formset in formsets:
            if not formset.is_valid():
                messages.error(self.request, formset.err_msg)
                return super().form_invalid(form)
        if self.object and self.object.type != lgc_models.QUOTATION:
            doc, deleted_docs = self.get_doc_forms()
            docs = lgc_models.DisbursementDocument.objects.filter(invoice=self.object)

            if lgc_views.check_docs(self, doc, docs) < 0:
                return super().form_invalid(form)

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
            if self.object and self.object.type != lgc_models.QUOTATION:
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
            return super().form_valid(form)

    def get_form(self, form_class=lgc_forms.InvoiceCreateForm):
        form = super().get_form(form_class=form_class)
        form.helper = FormHelper()
        form.helper.form_tag = False
        gen_invoice_html = None

        if self.object:
            state_div = Div('state', css_class='form-group col-md-2')
            if self.object.type == lgc_models.QUOTATION and self.object.process:
                gen_invoice_html = HTML(('&nbsp;<a href="' +
                                         str(reverse_lazy('lgc-gen-invoice',
                                                          kwargs={'pk':self.object.id})) +
                                         '" class="btn btn-outline-info">' +
                                         _('Generate invoice') + '</a>'))
        else:
            state_div = None
        layout = Layout(
            Div('version'), Div('client_update'), Div('client'),
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
                css_class='collapse', id='collapsePO'),
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
        if self.object:
            layout.append(
                Div(
                    Div('already_paid',
                        css_class='form-group col-md-2 border-left border-top border-bottom'),
                    Div('already_paid_desc',
                        css_class='form-group col-md-2 border-right border-top border-bottom'),
                    css_class='form-row')
            )
        layout.append(Div(
            Div(HTML('&nbsp;'), css_class='form-group col-md-2'),
            css_class='form-row'),
        )
        layout.append(Div(
            Div(HTML(get_template(CURRENT_DIR,
                                  'lgc/billing_formsets_template.html')),
                css_class='form-group col-md-9'),
            css_class='form-row')
        )
        if self.object and self.object.type != lgc_models.QUOTATION:
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

        if self.object:
            layout.append(Div('number'))
            action = _('Update')
        else:
            action = _('Create')
        layout.append(HTML('<button class="btn btn-outline-info" type="submit" ' +
                           'onclick="return form_checks();">' + action + '</button>'))
        layout.append(gen_invoice_html)

        form.helper.layout = layout
        return form

class InvoiceCreateView(InvoiceCommonView, SuccessMessageMixin, CreateView):
    title = _('New Invoice')
    success_message = _('Invoice successfully created.')

    def get_context_data(self, **kwargs):
        if self.request.GET.get('quote') == '1':
            self.title = _('New quotation')
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        if self.request.GET.get('quote') == '1':
            objs = lgc_models.Invoice.objects.filter(type=lgc_models.QUOTATION)
        else:
            objs = lgc_models.Invoice.objects.filter(type=lgc_models.INVOICE)
        max_number = objs.all().aggregate(Max('number'))
        if max_number['number__max'] == None:
            invoice_number = 1
        else:
            invoice_number = max_number['number__max'] + 1

        form.instance.number = invoice_number
        try:
            return super().form_valid(form)
        except Exception as e:
            """Handle mysql duplicate error."""
            if e.args[0] == 1062:
                messages.error(self.request,
                               _('An invoice for this process already exists.'))
            else:
                messages.error(self.request, e.args[1])
            return super().form_invalid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

class InvoiceUpdateView(InvoiceCommonView, SuccessMessageMixin, UpdateView):
    title = _('Update Invoice')
    success_message = _('Invoice successfully updated.')

    def get_context_data(self, **kwargs):
        if self.object.type == lgc_models.QUOTATION:
            self.title = _('Update quotation')
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
    set_bold_search_attrs(objs, term, ['first_name', 'last_name', 'company'])
    objs = objs[:10]
    context = {
        'objects': objs
    }
    return render(request, 'lgc/client_search.html', context)

@login_required
def ajax_invoice_search_view(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()
    if not request.user.billing:
        return http.HttpResponseForbidden()

    term = request.GET.get('term', '')
    term_int = None
    objs = lgc_models.Invoice.objects

    objs = (objs.filter(email__istartswith=term)|
            objs.filter(first_name__istartswith=term)|
            objs.filter(last_name__istartswith=term)|
            objs.filter(company__istartswith=term))

    try:
        term_int = int(term)
        objs = lgc_models.Invoice.objects.filter(number__istartswith=term_int)
    except:
        pass
    set_bold_search_attrs(objs, term, term_int,
                          ['first_name', 'last_name', 'company', 'email', 'number'])
    objs = objs[:10]
    context = {
        'objects': objs
    }
    return render(request, 'lgc/invoice_search.html', context)

@login_required
def invoice_insert_client(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()
    if not request.user.billing:
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

class InvoiceItemCommonView(BillingTest):
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

    def get_form(self):
        if self.model == lgc_models.Item:
            form_class = lgc_forms.ItemForm
        else:
            form_class = lgc_forms.DisbursementForm
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
            rate_div = Div(Div('rate_eur', css_class='form-group col-md-1'),
                           Div('rate_usd', css_class='form-group col-md-1'),
                           Div('rate_cad', css_class='form-group col-md-1'),
                           Div('rate_gbp', css_class='form-group col-md-1'),
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
            context['settings'] = lgc_models.Settings.objects.all()[0]
            return context

        for obj in context['object_list']:
            attr = 'rate_' + currency.lower()
            if hasattr(obj, attr):
                obj.rate = getattr(obj, attr)
        context['type'] = 'item'
        return context

class InvoiceItemCreateView(InvoiceItemCommonView, CreateView):
    title = _('Insert Item')

class InvoiceItemUpdateView(InvoiceItemCommonView, UpdateView):
    title = _('Update Item')
    edit_expanded = True

class InvoiceDisbursementCommon():
    model = lgc_models.Disbursement
    delete_url = 'lgc-delete-disbursement'
    update_url = 'lgc-update-disbursement'
    success_url = 'lgc-insert-disbursement'

class InvoiceDisbursementCreateView(InvoiceDisbursementCommon,
                                    InvoiceItemCommonView, CreateView):
    title = _('Insert Disbursement')

class InvoiceDisbursementUpdateView(InvoiceDisbursementCommon,
                                    InvoiceItemUpdateView):
    title = _('Update Disbursement')

@login_required
def __invoice_item_delete_view(request, model, url, pk=None):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()
    if not request.user.billing:
        return http.HttpResponseForbidden()

    if not pk:
        return redirect(url)
    obj = model.objects.filter(id=pk)
    if len(obj) != 1:
        return redirect(url)
    obj = obj[0]
    obj.delete()
    params = get_url_params(request)
    messages.success(request, _('Item %(item)s successfully deleted.'%
                                {'item':obj.title}))
    return redirect(url + params)

def invoice_item_delete_view(request, pk=None):
    url = reverse_lazy('lgc-insert-item')
    return __invoice_item_delete_view(request, lgc_models.Item, url, pk)

def invoice_disbursement_delete_view(request, pk=None):
    url = reverse_lazy('lgc-insert-disbursement')
    return __invoice_item_delete_view(request, lgc_models.Disbursement, url, pk)

@login_required
def generate_invoice_from_quote(request, pk):
    if not request.user.billing:
        return http.HttpResponseForbidden()

    invoice_objs = lgc_models.Invoice.objects.filter(type=lgc_models.INVOICE)
    quote = lgc_models.Invoice.objects.filter(type=lgc_models.QUOTATION).filter(id=pk)
    if len(quote) != 1:
        raise Http404
    quote = quote[0]
    max_number = invoice_objs.all().aggregate(Max('number'))
    if max_number['number__max'] == None:
        max_number = 1
    else:
        max_number = max_number['number__max'] + 1
    quote.process = None
    quote.save()

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

    return redirect('lgc-invoice', quote.id)
