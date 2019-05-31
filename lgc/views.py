import pdb                # pdb.set_trace()
from django.db import transaction
from django.forms import formset_factory, modelformset_factory
from common.utils import (pagination, lgc_send_email, must_be_staff,
                          set_bold_search_attrs, get_template)
import common.utils as utils
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

contact_admin_str = _('Please contact your administrator.')
delete_str = _('Delete')

User = get_user_model()
CURRENT_DIR = Path(__file__).parent


def token_generator():
    size = 64
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits

    while True:
        r = ''.join(random.choice(chars) for _ in range(size))
        if len(User.objects.filter(token=r)) == 0:
            return r

def save_active_tab(obj):
    obj.request.session['active_tab'] = obj.request.POST.get('active_tab')

def set_active_tab(obj, context):
    active_tab = obj.request.session.get('active_tab')
    if active_tab:
        del obj.request.session['active_tab']
        context['form'].fields['active_tab'].initial = active_tab

@login_required
def home(request):
    context = {
        'title': (_('Welcome %(first_name)s %(last_name)s')%
                  {'first_name':request.user.first_name,
                   'last_name':request.user.last_name}),
    }

    if request.user.role == user_models.EMPLOYEE:
        return render(request, 'employee/home.html', context)

    if request.user.role in user_models.get_hr_roles():
        return render(request, 'hr/home.html', context)

    if request.user.role in user_models.get_internal_roles():
        employees = user_models.get_employee_user_queryset().filter(status=user_models.USER_STATUS_PENDING).count()
        hrs = user_models.get_hr_user_queryset().filter(status=user_models.USER_STATUS_PENDING).count()
        files = lgc_models.Person.objects.count()
        context['nb_pending_employees'] = employees
        context['nb_pending_hrs'] = hrs
        context['nb_files'] = files
        expirations = lgc_models.Expiration.objects.filter(person__responsible=request.user).filter(enabled=True).order_by('end_date')
        compare_date = (timezone.now().date() +
                        datetime.timedelta(days=settings.EXPIRATIONS_NB_DAYS))
        context['nb_expirations'] = len(expirations.filter(end_date__lte=compare_date))

        return render(request, 'lgc/home.html', context)

    return http.HttpResponseForbidden()

@login_required
def tables(request):
    return render(request, 'lgc/tables.html', {'title':'Tables'})

class UserTest(UserPassesTestMixin):
    def test_func(self):
        if not self.is_update:
            return self.request.user.role in user_models.get_internal_roles()

        self.object = self.get_object()
        """ Employee check """
        if (self.request.user.role == user_models.EMPLOYEE and
            self.object.user == self.request.user):
            return True

        """ HR check """
        if (self.request.user.role in user_models.get_hr_roles() and
            self.object.user in self.request.user.hr_employees.all()):
            return True

        """ Internal user check """
        if self.request.user.role not in user_models.get_internal_roles():
            return False
        if (self.request.user.role == user_models.JURIST and
            (not self.request.user in self.object.responsible.all())):
            return False
        return True

class PersonCommonListView(LoginRequiredMixin, UserTest, ListView):
    template_name = 'lgc/sub_generic_list_with_search_form.html'
    model = lgc_models.Person
    ajax_search_url = reverse_lazy('lgc-file-search-ajax')
    search_url = reverse_lazy('lgc-files')
    update_url = 'lgc-file'
    process_col = None

    class Meta:
        abstract = True

    def get_ordering(self):
        return self.request.GET.get('order_by', '-id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Files')
        context['update_url'] = self.update_url
        context['ajax_search_url'] = self.ajax_search_url
        context['search_url'] = self.search_url

        context['item_url'] = 'lgc-file'
        context['header_values'] = [('ID', 'id', 'is_private', _('<i>(private)</i>')),
                                    (_('First Name'), 'first_name'),
                                    (_('Last Name'), 'last_name'), ('E-mail', 'email'),
                                    (_('Birth Date'), 'birth_date'),
                                    (_('Created'), 'creation_date')]

        if self.request.user.role == user_models.CONSULTANT:
            context['create_url'] = reverse_lazy('lgc-file-create')

        p = pagination(self.request, context, reverse_lazy('lgc-files'))
        if self.model == user_models.User or self.process_col == None:
            return p

        prev_id = None
        proc_idx = 0
        for obj in p['object_list']:
            if obj.id == prev_id:
                proc_idx += 1
            else:
                proc_idx = 0
                prev_id = obj.id
                qs = obj.personprocess_set.filter(active=self.process_col)

            if len(qs) == 0:
                print('cannot get person process')
                continue
            proc = qs[proc_idx]
            if translation.get_language() == 'fr':
                obj.proc = proc.name_fr
            else:
                obj.proc = proc.name_en

        context['header_values'] += [('Process', 'proc')]

        return p

    def test_func(self):
        return self.request.user.role in user_models.get_internal_roles()

class PersonListView(PersonCommonListView):
    def match_extra_terms(self, objs):
        id = self.request.GET.get('id', '')
        info_process = self.request.GET.get('info_process', '')
        state = self.request.GET.get('state', '')
        jurist = self.request.GET.get('jurist', '')
        consultant = self.request.GET.get('consultant', '')
        prefecture = self.request.GET.get('prefecture', '')
        subprefecture = self.request.GET.get('subprefecture', '')
        consulate = self.request.GET.get('consulate', '')
        direccte = self.request.GET.get('direccte', '')
        jurisdiction = self.request.GET.get('jurisdiction', '')
        start_date = self.request.GET.get('start_date', '')
        process_state = self.request.GET.get('process_state', '')

        if process_state == 'A':
            objs = objs.filter(personprocess_set__active=True)
            self.process_col = True
        elif process_state == 'I':
            objs = objs.filter(personprocess_set__active=False)
            self.process_col = False

        if id:
            objs = objs.filter(id=id)

        if info_process:
            objs = objs.filter(info_process__iexact=info_process)
        if state:
            objs = objs.filter(state__exact=state)
        if jurist:
            o = User.objects.filter(id=jurist)
            if len(o):
                objs = objs.filter(responsible__in=o)
        if consultant:
            o = User.objects.filter(id=consultant)
            if len(o):
                objs = objs.filter(responsible__in=o)
        if prefecture:
            objs = objs.filter(prefecture__exact=prefecture)
        if subprefecture:
            objs = objs.filter(subprefecture__exact=subprefecture)
        if consulate:
            objs = objs.filter(consulate__exact=consulate)
        if direccte:
            objs = objs.filter(direccte__exact=direccte)
        if jurisdiction:
            objs = objs.filter(jurisdiction__exact=jurisdiction)
        if start_date:
            objs = objs.filter(start_date=utils.parse_date(start_date))
        return objs

    def get_queryset(self):
        term = self.request.GET.get('term', '')
        order_by = self.get_ordering()
        objs = self.match_extra_terms(lgc_models.Person.objects)

        if term == '':
            return objs.order_by(order_by)

        objs = (objs.filter(email__istartswith=term)|
                objs.filter(first_name__istartswith=term)|
                objs.filter(last_name__istartswith=term))
        return objs.order_by(order_by)

    def get_search_form(self):
        if len(self.request.GET):
            form = lgc_forms.PersonSearchForm(self.request.GET)
        else:
            form = lgc_forms.PersonSearchForm()

        form.helper = FormHelper()
        form.helper.form_tag = False
        form.helper.form_method = 'get'
        form.helper.layout = Layout(
            Div(
                Div('id', css_class='form-group col-md-3'),
                Div('info_process', css_class='form-group col-md-3'),
                Div('state', css_class='form-group col-md-3'),
                Div('jurist', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(
                Div('consultant', css_class='form-group col-md-3'),
                Div('prefecture', css_class='form-group col-md-3'),
                Div('subprefecture', css_class='form-group col-md-3'),
                Div('consulate', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(
                Div('direccte', css_class='form-group col-md-3'),
                Div('jurisdiction', css_class='form-group col-md-3'),
                Div('start_date', css_class='form-group col-md-3'),
                Div('process_state', css_class='form-group col-md-3'),
                css_class='form-row'),
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = self.get_search_form()
        return context

def local_user_get_person_form_layout(user, form, action, obj,
                                      completed_processes):
    external_profile = None
    form.helper = FormHelper()
    form.helper.form_tag = False

    info_tab = LgcTab(
        _('Information'),
        Div(Div('is_private'), css_class='form-row'),
        Div(Div('active_tab'),
            Div('first_name', css_class='form-group col-md-4'),
            Div('last_name', css_class='form-group col-md-4'),
            Div('version'),
            css_class='form-row'),
        Div(Div('email', css_class='form-group col-md-4'),
            Div('citizenship', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('foreigner_id', css_class='form-group col-md-4'),
            Div('birth_date', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('info_process', css_class='form-group col-md-4'),
            Div('responsible', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('work_permit', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('passport_expiry', css_class='form-group col-md-4'),
            Div('passport_nationality', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div(HTML('<hr>'), css_class='form-group col-md-8'),
            css_class='form-row'),
        Div(Div('home_entity', css_class='form-group col-md-4'),
            Div('host_entity', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('home_entity_address', css_class='form-group col-md-4'),
            Div('host_entity_address', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('local_address', css_class='form-group col-md-4'),
            Div('local_phone_number', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('foreign_address', css_class='form-group col-md-4'),
            Div('foreign_phone_number', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('foreign_country', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div(HTML('<hr>'), css_class='form-group col-md-8'),
            css_class='form-row'),
        Div(Div('spouse_first_name', css_class='form-group col-md-4'),
            Div('spouse_last_name', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('spouse_birth_date', css_class='form-group col-md-4'),
            Div('spouse_citizenship', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('spouse_passport_expiry', css_class='form-group col-md-4'),
            Div('spouse_passport_nationality', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div(HTML('<hr>'), css_class='form-group col-md-8'),
            css_class='form-row'),
        Div(Div('prefecture', css_class='form-group col-md-4'),
            Div('subprefecture', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('consulate', css_class='form-group col-md-4'),
            Div('direccte', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('jurisdiction', css_class='form-group col-md-4'),
            css_class='form-row'),
    )

    info_tab.append(Div(Div(HTML(get_template(CURRENT_DIR,
                                              'lgc/formsets_template.html')),
                            css_class='form-group col-md-10'),
                        css_class='form-row'))
    info_tab.append(Div(Div('state', css_class='form-group col-md-4'),
                        Div('start_date', css_class='form-group col-md-4'),
                        css_class='form-row'))
    info_tab.append(Div(Div('comments', css_class='form-group col-md-8'),
            css_class='form-row'))

    tab_holder = TabHolder(info_tab)

    if obj:
        external_profile = LgcTab(_('Account Profile'))
        if obj.user:
            html = (_("Click here to manage this person's account profile: ") +
                    '&nbsp;<a href="' +
                    str(reverse_lazy('lgc-account', kwargs={'pk': obj.user.id})) +
                    '">' + _('update profile') + '</a><br><br>')
        else:
            html = (_('The profile for this person does not exist. Follow this link to create it: ') +
                    '&nbsp;<a href="' +
                    str(reverse_lazy('lgc-account-link', kwargs={'pk': obj.id})) +
                    '">' + _('create profile') + '</a><br><br>')
        external_profile.append(Div(HTML(html), css_class='form-row'))

    if obj:
        process_tab = LgcTab(_('Processes'))
        if completed_processes:
            process_tab.append(HTML('<a href="' +
                                    str(reverse_lazy('lgc-person-processes',
                                                     kwargs={'pk': obj.id})) +
                                    '">Completed processes (' +
                                    str(len(completed_processes)) +
                                    ')</a><hr><br>'))

        process_tab.append(Div(Div('process_name', css_class='form-group col-md-3'),
                               HTML('<div class="form-group"><label for="id_process_name" class="col-form-label">&nbsp;</label><div class=""><button class="btn btn-outline-info" type="submit">' + _('Create') + '</button></div></div>'),
                               css_class='form-row'))

        process_tab.append(
            HTML(get_template(CURRENT_DIR, 'lgc/person_process_list.html')))
        tab_holder.append(process_tab)

        if obj.invoice_set.count():
            billing_tab = LgcTab(_('Billing'))
            billing_tab.append(HTML(get_template(CURRENT_DIR, 'lgc/file_invoice_list.html')))
            tab_holder.append(billing_tab)

    documents_tab = LgcTab(_('Documents'))
    documents_tab.append(HTML(get_template(CURRENT_DIR,
                                           'lgc/document_form.html')))

    if external_profile != None:
        tab_holder.append(external_profile)

    tab_holder.append(documents_tab)

    layout = Layout(tab_holder)
    layout.append(HTML('<button class="btn btn-outline-info" type="submit">' +
                       action + '</button>'))
    if obj and user.is_staff:
        layout.append(HTML('&nbsp;<a href="' +
                           str(reverse_lazy('lgc-file-delete', kwargs={'pk': obj.id})) +
                           '"class="btn btn-outline-info">' +
                           _('Delete') + '</a>'))
    form.helper.layout = layout
    return form

def employee_user_get_person_form_layout(form, action, obj):
    external_profile = None
    form.helper = FormHelper()
    form.helper.form_tag = False
    if obj == None or obj.user == None:
        return None

    info_tab = LgcTab(
        _('Information'),
        Div(Div('active_tab'),
            Div('first_name', css_class='form-group col-md-4'),
            Div('last_name', css_class='form-group col-md-4'),
            Div('version'),
            css_class='form-row'),
        Div(Div('email', css_class='form-group col-md-4'),
            Div('citizenship', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('foreigner_id', css_class='form-group col-md-4'),
            Div('birth_date', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('passport_expiry', css_class='form-group col-md-4'),
            Div('passport_nationality', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('home_entity', css_class='form-group col-md-4'),
            Div('host_entity', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('home_entity_address', css_class='form-group col-md-4'),
            Div('host_entity_address', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('local_address', css_class='form-group col-md-4'),
            Div('local_phone_number', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('foreign_address', css_class='form-group col-md-4'),
            Div('foreign_phone_number', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('foreign_country', css_class='form-group col-md-4'),
            css_class='form-row'),
    )

    info_tab.append(Div(Div(HTML(get_template(CURRENT_DIR,
                                              'lgc/formsets_template.html')),
                            css_class='form-group col-md-10'),
                        css_class='form-row'))

    tab_holder = TabHolder(info_tab)
    process_tab = LgcTab(_('Processes'))
    process_tab.append(HTML(get_template(CURRENT_DIR, 'lgc/person_process_list.html')))
    tab_holder.append(process_tab)

    documents_tab = LgcTab(_('Documents'))
    documents_tab.append(HTML(get_template(CURRENT_DIR, 'lgc/document_form.html')))
    tab_holder.append(documents_tab)

    layout = Layout(tab_holder)
    layout.append(HTML('<button class="btn btn-outline-info" type="submit">' +
                       action + '</button>'))
    form.helper.layout = layout
    return form

def get_person_form_layout(cur_user, form, action, obj,
                           completed_processes=None):
    if cur_user.role in user_models.get_internal_roles():
        return local_user_get_person_form_layout(cur_user, form, action, obj,
                                                 completed_processes)
    if cur_user.role == user_models.EMPLOYEE:
        return employee_user_get_person_form_layout(form, action, obj)
    if cur_user.role in user_models.get_hr_roles():
        return employee_user_get_person_form_layout(form, action, obj)
    return None

def hr_add_employee(form_data, user_object):
    if user_object == None:
        return

    user_object.hr_employees.clear()

    if 'HR' not in form_data:
        return
    for i in form_data['HR']:
        h = user_models.get_hr_user_queryset().filter(id=i.id)
        if not h:
            return
        h = h.get()
        if not h:
            return
        h.hr_employees.add(user_object.id)
        h.save()

class TemplateTimelineStages():
    is_done = False
    name = ''
    start_date = ''

def check_docs(obj, doc, docs):
    if not doc.is_valid():
        messages.error(self.request, _('Invalid document.'))
        return -1
    if doc.cleaned_data['document'] == None:
        return 0
    if doc.cleaned_data['description'] == '':
        messages.error(obj.request,
                       _('Invalid document description.'))
        return -1
    if doc.instance.document.size > settings.MAX_FILE_SIZE << 20:
        messages.error(obj.request,
                       _('File too big. Maximum file size is %dM.')%
                       settings.MAX_FILE_SIZE)
        return -1
    for d in docs.all():
        if d.document.name != doc.instance.document.name:
            continue
        messages.error(obj.request, _("File `%s' already exists.")%
                       d.document.name)
        return -1
    return 0

class PersonCommonView(LoginRequiredMixin, UserTest, SuccessMessageMixin):
    model = lgc_models.Person
    is_update = False
    template_name = 'lgc/generic_form_with_formsets.html'
    success_url = 'lgc-file'
    form_diff = []
    is_children_diff = False
    is_expirations_diff = False
    is_spouse_expirations_diff = False
    is_archive_box_diff = False

    def get_success_url(self):
        return reverse_lazy(self.success_url, kwargs={'pk': self.object.id})

    def get_active_person_processes(self):
        if self.object == None:
            return

        if type(self.object).__name__ == 'Employee':
            object = self.object.user.person_user_set
        else:
            object = self.object

        return object.personprocess_set.filter(active=True)

    def get_timeline_stages(self, person_process):
        process_common = ProcessCommonView()
        timeline_stages = []
        for s in person_process.stages.all():
            timeline_stage = TemplateTimelineStages()
            timeline_stage.is_done = True
            if translation.get_language() == 'fr':
                timeline_stage.name = s.name_fr
            else:
                timeline_stage.name = s.name_en
            timeline_stage.validation_date = s.validation_date
            timeline_stages.append(timeline_stage)

        to_skip = person_process.stages.filter(is_specific=False).count()
        stages = process_common.get_ordered_stages(person_process.process)
        for s in stages:
            if to_skip:
                to_skip -= 1
                continue
            timeline_stage = TemplateTimelineStages()
            if translation.get_language() == 'fr':
                timeline_stage.name = s.name_fr
            else:
                timeline_stage.name = s.name_en
            timeline_stages.append(timeline_stage)

        return timeline_stages

    def set_person_formsets_data(self, formsets):
        formsets[0].title = _('Children')
        formsets[0].id = 'children_id'
        formsets[0].err_msg = _('Invalid Children table')

        if self.request.user.role in user_models.get_internal_roles():
            formsets[1].title = _('Visas / Residence Permits / Work Permits')
            formsets[1].id = 'expiration_id'
            formsets[1].err_msg = _('Invalid Visas / Residence Permits / Work Permits table')

            formsets[2].title = _('Spouse Visas / Residence Permits / Work Permits')
            formsets[2].id = 'spouse_expiration_id'
            formsets[2].err_msg = _('Invalid Spouse Visas / Residence Permits / Work Permits table')

            formsets[3].title = _('Archive boxes')
            formsets[3].id = 'ab_id'
            formsets[3].err_msg = _('Invalid archive box number')

    def get_person_formsets(self):
        formsets = []

        if self.request.user.role in user_models.get_internal_roles():
            forms = lgc_forms
            models = lgc_models
            ArchiveBoxFormSet = modelformset_factory(models.ArchiveBox,
                                                     form=lgc_forms.ArchiveBoxForm,
                                                     can_delete=True)

            ExpirationFormSet = modelformset_factory(models.Expiration,
                                                     form=forms.ExpirationForm,
                                                     can_delete=True)
            SpouseExpirationFormSet = modelformset_factory(models.Expiration,
                                                           form=forms.SpouseExpirationForm,
                                                           can_delete=True)

        else:
            forms = employee_forms
            models = employee_models

        ChildrenFormSet = modelformset_factory(models.Child,
                                               form=forms.ChildCreateForm,
                                               can_delete=True)
        if self.request.POST:
            formsets.append(ChildrenFormSet(self.request.POST, prefix='children'))
            if self.request.user.role in user_models.get_internal_roles():
                formsets.append(ExpirationFormSet(self.request.POST, prefix='expiration'))
                formsets.append(SpouseExpirationFormSet(self.request.POST, prefix='spouse_expiration'))
                formsets.append(ArchiveBoxFormSet(self.request.POST, prefix='ab'))
            self.set_person_formsets_data(formsets)
            return formsets

        if self.is_update:
            children_queryset = models.Child.objects.filter(person=self.object)
            if self.request.user.role in user_models.get_internal_roles():
                expiration_queryset = models.Expiration.objects.filter(person=self.object).filter(type__in=lgc_models.get_expiration_list())
                spouse_expiration_queryset = models.Expiration.objects.filter(person=self.object).filter(type__in=lgc_models.get_spouse_expiration_list())
                archive_box_queryset = lgc_models.ArchiveBox.objects.filter(person=self.object.id)
        else:
            children_queryset = models.Child.objects.none()
            if self.request.user.role in user_models.get_internal_roles():
                expiration_queryset = models.Expiration.objects.none()
                spouse_expiration_queryset = models.Expiration.objects.none()
                archive_box_queryset = lgc_models.ArchiveBox.objects.none()
        child_formset = ChildrenFormSet(queryset=children_queryset,
                                        prefix='children')
        for form in child_formset.forms:
            if (self.object and type(self.object).__name__ != 'Employee' and
                hasattr(form.instance, 'expiration') and
                form.instance.expiration):
                form.fields['dcem_end_date'].initial = form.instance.expiration.end_date
                form.fields['dcem_enabled'].initial = form.instance.expiration.enabled
        formsets.append(child_formset)

        if self.request.user.role in user_models.get_internal_roles():
            formsets.append(ExpirationFormSet(queryset=expiration_queryset,
                                              prefix='expiration'))
            formsets.append(SpouseExpirationFormSet(queryset=spouse_expiration_queryset,
                                                    prefix='spouse_expiration'))
            formsets.append(ArchiveBoxFormSet(queryset=archive_box_queryset,
                                              prefix='ab'))

        self.set_person_formsets_data(formsets)
        return formsets

    def set_person_process_stages(self, context):
        active_processes = self.get_active_person_processes()
        context['active_processes'] = []
        if active_processes == None:
            return
        for person_process in active_processes.all():
            form = lgc_forms.PersonProcessForm(instance=person_process)
            form.fields['no_billing'].widget.attrs['disabled'] = True
            form.fields['consulate'].widget.attrs['disabled'] = True
            form.fields['prefecture'].widget.attrs['disabled'] = True
            person_process.form = form
            person_process.timeline_stages = self.get_timeline_stages(person_process)
            if self.request.user.role in user_models.get_internal_roles():
                person_process.edit_url = reverse_lazy('lgc-person-process',
                                                       kwargs={'pk':person_process.id})
            context['active_processes'].append(person_process)

    def get_formset_objs(self, queryset, show_dcem=False):
        obj_lists = []
        key_list = []
        first_loop = True

        for o in queryset:
            obj_list = []
            for k in o.__dict__.keys():
                if (k == 'id' or k == '_state' or k == 'person_id' or
                    k == 'person_child_id' or
                    (show_dcem == False and k == 'expiration_id')):
                    continue
                if first_loop:
                    k_verbose_name = o._meta.get_field(k).verbose_name.title()
                    key_list += [k_verbose_name]
                    if k == 'expiration_id':
                        key_list += [_('Enabled')]
                attr = 'get_' + k + '_display'
                if hasattr(o, attr):
                    v = getattr(o, attr)
                else:
                    v = getattr(o, k)
                if show_dcem and k == 'expiration_id':
                    if v:
                        v = o.expiration.end_date
                        obj_list += [v]
                        v = o.expiration.enabled
                    else:
                        obj_list += ['']
                        v = False
                    k = 'enabled'

                if k == 'enabled':
                    if v:
                        v = _('Yes')
                    else:
                        v = _('No')
                obj_list += [v]
            obj_lists.append(obj_list)
            first_loop = False
        return (key_list, obj_lists)

    def get_doc_forms(self):
        DocumentFormSet = modelformset_factory(lgc_models.Document,
                                               form=lgc_forms.DocumentFormSet,
                                               can_delete=True, extra=0)

        doc = lgc_forms.DocumentForm(self.request.POST, self.request.FILES)
        deleted_docs = DocumentFormSet(self.request.POST, self.request.FILES,
                                       prefix='docs')
        return (doc, deleted_docs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['form_diff'] = self.form_diff
        context['formsets_diff'] = []

        context['formsets'] = self.get_person_formsets()
        model = self.get_model(self.object)
        if self.is_children_diff:
            """Do not show the DCEM expiration in employee view."""
            if model == employee_models:
                show_dcem = False
            else:
                show_dcem = True
            context['formsets_diff'] += [('children', _('Children'),
                                          self.get_formset_objs(model.Child.objects.filter(person=self.object), show_dcem=show_dcem))]
        if self.is_expirations_diff:
            context['formsets_diff'] += [('expiration', _('Expirations'),
                                          self.get_formset_objs(model.Expiration.objects.filter(person=self.object).filter(type__in=lgc_models.get_expiration_list())))]
        if self.is_spouse_expirations_diff:
            context['formsets_diff'] += [('spouse_expiration', _('Spouse Expirations'),
                                          self.get_formset_objs(model.Expiration.objects.filter(person=self.object).filter(type__in=lgc_models.get_spouse_expiration_list())))]
        if self.is_archive_box_diff:
            context['formsets_diff'] += [('ab', _('Archive boxes'),
                                          self.get_formset_objs(lgc_models.ArchiveBox.objects.filter(person=self.object)))]
        if self.form_diff or len(context['formsets_diff']):
            changes_form = lgc_forms.ChangesDetectedForm()
            changes_form.helper = FormHelper()
            changes_form.helper.form_tag = False

            context['changes_detected_form'] = changes_form

        DocumentFormSet = modelformset_factory(lgc_models.Document,
                                               form=lgc_forms.DocumentFormSet,
                                               can_delete=True, extra=0)

        if self.object:
            if self.request.user.role in user_models.get_internal_roles():
                obj = self.object
            else:
                emp_obj = self.get_object()
                obj = emp_obj.user.person_user_set
            context['docs'] = DocumentFormSet(prefix='docs', queryset=lgc_models.Document.objects.filter(person=obj))
            context['process'] = lgc_models.PersonProcess.objects.filter(person=obj)
            if self.request.user.role in user_models.get_internal_roles():
                pending_invoices = self.object.invoice_set.filter(state=lgc_models.INVOICE_STATE_PENDING)|self.object.invoice_set.filter(state=lgc_models.INVOICE_STATE_TOBEDONE).all()
                closed_invoices = self.object.invoice_set.exclude(state=lgc_models.INVOICE_STATE_PENDING).exclude(state=lgc_models.INVOICE_STATE_TOBEDONE).all()
                context['invoice_set'] = [
                    (pending_invoices, _('Pending Invoices'), 'pending_id'),
                    (closed_invoices, _('Closed Invoices'), 'closed_id')
                ]

        self.set_person_process_stages(context)
        set_active_tab(self, context)

        context['doc'] = lgc_forms.DocumentForm()
        if self.request.user.role in user_models.get_internal_roles():
            context['show_detailed_process'] = True

        return context

    def save_formset_instances(self, instances):
        for i in instances:
            if i.person_id and i.person_id != self.object.id:
                continue
            i.person = self.object
            i.save()

    def save_expiration(self, form):
        if type(self.object).__name__ == 'Employee':
            return

        if form.cleaned_data.get('dcem_end_date') == None:
            if (hasattr(form.instance, 'employee_child_set') and
                form.instance.employee_child_set):
                form.instance.employee_child_set.expiration = None
            if form.instance.expiration:
                form.instance.expiration.delete()
                form.instance.expiration = None
            return

        if form.instance.expiration:
            expiration = form.instance.expiration
        else:
            expiration = lgc_models.Expiration()

        expiration.end_date = form.cleaned_data['dcem_end_date']
        expiration.enabled = form.cleaned_data['dcem_enabled']
        expiration.person = self.object
        expiration.type = lgc_models.EXPIRATION_TYPE_DCEM
        expiration.save()
        form.instance.expiration = expiration

    def save_formset(self, formset):
        if formset.id != 'children_id':
            instances = formset.save(commit=False)
            self.save_formset_instances(instances)
            return
        """
        Instead of doing:
          instances = formset.save(commit=False)
          self.save_formset_instances(instances)
        Let's walk through all forms and look for child expirations and
        save them if they are present.
        """

        for form in formset.forms:
            if len(form.cleaned_data) == 0 or form.cleaned_data['DELETE']:
                continue

            self.save_expiration(form)
            form.instance.person = self.object
            form.instance.save()

    def delete_formset(self, formset):
        for obj in formset.deleted_forms:
            if (obj.instance.id != None and
                obj.instance.person_id == self.object.id):
                """
                Do not delete DCEM expirations when handling Employee Children.
                These are still referenced by Person Children.
                """
                if (type(self.object).__name__ != 'Employee' and
                    hasattr(obj.instance, 'expiration') and
                    obj.instance.expiration):
                    obj.instance.expiration.delete()

                if hasattr(obj.instance, 'employee_child') and obj.instance.employee_child:
                    obj.instance.employee_child.delete()
                obj.instance.delete()

    def clear_related_objects(self, objs):
        for o in objs:
            o.delete()

    def copy_related_object(self, src, dst, keys_from):
        for k in keys_from.__dict__.keys():
            if (k == '_state' or k == 'id' or k == 'person_id' or k == 'updated' or
                k == 'version'):
                continue
            try:
                setattr(dst, k, getattr(src, k))
            except:
                pass

    def have_objs_changed(self, formset, old_objs):
        new_objs = []

        for form in formset.forms:
            if form.empty_permitted:
                continue
            if not hasattr(form, 'cleaned_data'):
                if not form.is_valid():
                    return True
            if form.cleaned_data.get('DELETE') == None:
                continue
            if form.instance.id and form.cleaned_data['DELETE']:
                continue

            new_objs.append(form.instance)

        if len(old_objs) != len(new_objs):
            return True

        for i in range(len(old_objs)):
            for k in old_objs[i].__dict__.keys():
                if k == 'id' or k == '_state' or k == 'person_id':
                    continue
                try:
                    if getattr(old_objs[i], k) != getattr(new_objs[i], k):
                        return True
                except:
                    pass
        return False

    def set_employee_data(self, form, formsets):
        if self.request.user.role not in user_models.get_internal_roles():
            return
        if type(self.object).__name__ == 'Employee':
            return

        if (not hasattr(self.object, 'user') or
            not hasattr(self.object.user, 'employee_user_set')):
            return

        employee = self.object.user.employee_user_set

        self.copy_related_object(self.object, employee, employee)
        employee.modified_by = self.request.user
        employee.modification_date = timezone.now()
        employee.version += 1
        employee.save()

        for formset in formsets:
            if formset.id != 'children_id':
                continue
            objs = employee_models.Child.objects.filter(person=self.object.user.employee_user_set).all()
            if not self.have_objs_changed(formset, objs):
                continue

            for form in formset.forms:
                if form.instance.id == None or form.cleaned_data['DELETE']:
                    continue
                if not hasattr(form.instance, 'employee_child_set'):
                    form.instance.employee_child_set = employee_models.Child()
                self.copy_related_object(form.instance,
                                         form.instance.employee_child_set,
                                         form.instance)
                form.instance.employee_child_set.person_id = employee.id
                form.instance.employee_child_set.expiration = form.instance.expiration
                form.instance.employee_child_set.save()

    def check_form_diff2(self, obj, form, cleaned_data, ignore_list=[]):
        form_diff = []

        for key in cleaned_data.keys():
            if key in ignore_list:
                continue
            if key == 'version' or key == 'user' or key == 'DELETE' or key == 'updated':
                continue
            try:
                val = getattr(obj, key)
            except:
                continue

            if cleaned_data[key] == val:
                continue

            attr = 'get_' + key + '_display'
            if hasattr(obj, attr):
                val = getattr(obj, attr)

            if form.fields[key].label:
                label = form.fields[key].label
            else:
                label = key.capitalize()

            if not hasattr(val, 'all'):
                form_diff.append((label, False, val))
                continue

            """ check all manyToMany objects """
            val = val.all()
            form_val = cleaned_data[key]
            for i in range(len(val)):
                if i + 1 > len(form_val) or val[i] != form_val[i]:
                    form_diff.append((label, True, val))
                    break
                continue

        return form_diff

    def check_formsets_diff(self, formsets, model):
        for formset in formsets:
            if formset.id == 'children_id':
                self.is_children_diff = self.have_objs_changed(formset,
                                                               model.Child.objects.filter(person=self.object))
            elif formset.id == 'expiration_id':
                self.is_expirations_diff = self.have_objs_changed(formset,
                                                                  model.Expiration.objects.filter(person=self.object).filter(type__in=lgc_models.get_expiration_list()))
            elif formset.id == 'spouse_expiration_id':
                self.is_spouse_expirations_diff = self.have_objs_changed(formset,
                                                                         model.Expiration.objects.filter(person=self.object).filter(type__in=lgc_models.get_spouse_expiration_list()))
            elif formset.id == 'ab_id':
                self.is_archive_box_diff = self.have_objs_changed(formset,
                                                                  model.ArchiveBox.objects.filter(person=self.object))
        return (self.is_children_diff or self.is_archive_box_diff or
                self.is_expirations_diff or self.is_spouse_expirations_diff)

    def get_model(self, obj):
        if self.object and type(self.object).__name__ == 'Employee':
            return employee_models
        return lgc_models

    def check_form_diff(self, obj, form, formsets, ignore_list=[]):
        if obj == None:
            return []

        if form.cleaned_data['version'] == obj.version:
            return False

        self.form_diff = self.check_form_diff2(obj, form, form.cleaned_data, ignore_list)
        formsets_diff = self.check_formsets_diff(formsets, self.get_model(obj))
        return len(self.form_diff) or formsets_diff

    def get_current_object(self):
        try:
            return self.get_object()
        except:
            return None

    def set_formset_diff_type(self, formset):
        if formset.id == 'children_id':
            self.is_children_diff = True
        elif formset.id == 'expiration_id':
            self.is_expirations_diff = True
        elif formset.id == 'spouse_expiration_id':
            self.is_spouse_expirations_diff = True
        elif formset.id == 'ab_id':
            self.is_archive_box_diff = True

    def are_formsets_valid(self, obj, formsets):
        are_valid = True

        for i in range(len(formsets)):
            formset = formsets[i]
            if formset.is_valid():
                continue

            for form in formset.forms:
                if form.errors.get('id', '') == '':
                    continue
                """
                A form that we modified has been deleted, treat it as new.
                """
                self.set_formset_diff_type(formset)
                del form.errors['id']
                form.is_valid()

            if not formset.is_valid():
                messages.error(obj.request, formset.err_msg)
                are_valid = False
                continue

            """
            If a form that we modified has been deleted, treat it as new.
            Note, that this will not delete forms added by the other user.
            """
            formsets[i].data = formset.data.copy()
            if formset.prefix != '':
                initial_forms_str = formset.prefix + '-INITIAL_FORMS'
            else:
                initial_forms_str = 'INITIAL_FORMS'
            initial_forms_int = int(formset.data[initial_forms_str])
            if initial_forms_int > 0:
                formsets[i].data[initial_forms_str] = str(initial_forms_int - 1)
            """Recreate the management form."""
            del formsets[i].management_form
            formsets[i].management_form

        return are_valid

    def rename_doc_dir(self, form, old_obj, new_obj):
        if ('first_name' not in form.changed_data and
            'last_name' not in form.changed_data and
            'birth_date' not in form.changed_data and
            'home_entity' not in form.changed_data and
            'host_entity' not in form.changed_data and
            'is_private' not in form.changed_data):
            return
        lgc_models.rename_person_doc_dir(old_obj, new_obj)

    def form_valid(self, form):
        formsets = self.get_person_formsets()
        self.object = self.get_current_object()
        save_active_tab(self)

        if self.object:
            if (self.request.user.role in user_models.get_internal_roles() and
                self.object.state != lgc_models.FILE_STATE_CLOSED and
                form.cleaned_data['state'] == lgc_models.FILE_STATE_CLOSED and
                self.get_active_person_processes()):
                messages.error(self.request,
                               _('This file cannot be closed as it has a pending process.'))
                return self.form_invalid(form)

            changes_action = self.request.POST.get('changes_action', '')
            if changes_action == lgc_forms.CHANGES_DETECTED_DISCARD:
                return redirect(self.get_success_url())

            if (type(self.object).__name__ != 'Employee' and
                self.object.user and
                hasattr(self.object.user, 'employee_user_set') and
                self.object.user.employee_user_set and
                self.object.user.employee_user_set.updated):
                msg = (_('There is a pending moderation on this file.') +
                       '<a href="' +
                       str(reverse_lazy('employee-moderation',
                                        kwargs={'pk':self.object.user.employee_user_set.id})) +
                       '"> ' + _('Click here to moderate it.</a>'))
                messages.error(self.request, mark_safe(msg))
                return super().form_invalid(form)

            if not self.are_formsets_valid(self, formsets):
                return super().form_invalid(form)

            if changes_action != lgc_forms.CHANGES_DETECTED_FORCE:
                if self.check_form_diff(self.object, form, formsets):
                    return super().form_invalid(form)

            form.instance.version = self.object.version + 1
            self.rename_doc_dir(form, self.object, form.instance)
        else:
            if not self.are_formsets_valid(self, formsets):
                return super().form_invalid(form)
            changes_action = None

        form.instance.modified_by = self.request.user
        form.instance.modification_date = timezone.now()

        if self.request.user.role in user_models.get_internal_roles():
            if form.instance.start_date == None:
                form.instance.start_date = str(datetime.date.today())
            person = form.instance
        else:
            form.instance.updated = True
            """self.object is valid as external users can only update the form."""
            person = self.object.user.person_user_set

        doc, deleted_docs = self.get_doc_forms()
        docs = lgc_models.Document.objects.filter(person=person)

        if self.is_update and self.object.user != None:
            form.instance.user = self.object.user

        if check_docs(self, doc, docs) < 0:
            return super().form_invalid(form)

        with transaction.atomic():
            self.object = form.save()

            if (self.request.user.role in user_models.get_internal_roles() and
                form.cleaned_data['process_name']):
                person_process = lgc_models.PersonProcess()
                person_process.person = self.object
                person_process.process = form.cleaned_data['process_name']
                person_process.consulate = form.cleaned_data['consulate']
                person_process.prefecture = form.cleaned_data['prefecture']
                person_process.name_fr = person_process.process.name_fr
                person_process.name_en = person_process.process.name_en
                person_process.save()

            for formset in formsets:
                self.delete_formset(formset)
                self.save_formset(formset)

            self.object = form.save()
            if form.instance.user:
                form.instance.user.first_name = form.instance.first_name
                form.instance.user.last_name = form.instance.last_name
                form.instance.user.email = form.instance.email

                if self.request.user.role in user_models.get_internal_roles():
                    form.instance.user.responsible.set(form.instance.responsible.all())
                    form.instance.user.save()

            if doc.cleaned_data['document'] != None:
                doc.instance = lgc_models.Document()
                doc.instance.document = doc.cleaned_data['document']
                doc.instance.description = doc.cleaned_data['description']
                doc.instance.person = person
                doc.instance.uploaded_by = self.request.user
                doc.save()

            self.set_employee_data(form, formsets)

            if self.is_update and deleted_docs:
                for d in deleted_docs.deleted_forms:
                    if d.instance.id == None:
                        continue
                    try:
                        lgc_models.delete_person_doc(form.instance, d.instance)
                    except Exception as e:
                        messages.error(self.request,
                                       _('Cannot delete the file `%(filename)s`'%{'filename':d.instance.filename}))
                        print(e)

        return super().form_valid(form)

    def get_form(self, form_class=lgc_forms.PersonCreateForm):
        if self.request.user.role in user_models.get_internal_roles():
            form_class = lgc_forms.PersonCreateForm
        else:
            form_class = employee_forms.EmployeeUpdateForm
        form = super().get_form(form_class=form_class)

        if not self.is_update:
            return get_person_form_layout(self.request.user, form,
                                          _('Create'), None)
        return get_person_form_layout(self.request.user, form, _('Update'),
                                      self.object,
                                      lgc_models.PersonProcess.objects.filter(person=self.object.id).filter(active=False))

    class Meta:
        abstract = True

class PersonCreateView(PersonCommonView, CreateView):
    title = _('New File')
    is_update = False
    success_message = _('File successfully created')

class PersonUpdateView(PersonCommonView, UpdateView):
    title = _('File')
    is_update = True
    success_message = _('File successfully updated')

class PersonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = lgc_models.Person
    obj_name = _('File')
    title = _('Delete File')
    template_name = 'lgc/person_confirm_delete.html'
    success_url = reverse_lazy('lgc-files')
    cancel_url = 'lgc-file'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['cancel_url'] = reverse_lazy(self.cancel_url,
                                             kwargs={'pk':self.object.id})
        if self.object and self.object.user == None:
            context['dont_inform'] = True
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_message = _("%(obj_name)s of %(firstname)s %(lastname)s deleted successfully."%{
            'obj_name':self.obj_name,
            'firstname':self.object.first_name,
            'lastname':self.object.last_name,
        })

        if type(self.object).__name__ == 'User':
            if hasattr(self.object, 'person_user_set'):
                person_obj = self.object.person_user_set
            else:
                person_obj = None
        else:
            person_obj = self.object

        if person_obj and person_obj.document_set:
            for doc in person_obj.document_set.all():
                doc.delete()
                os.remove(os.path.join(settings.MEDIA_ROOT,
                                       doc.document.name))

        if (self.object.user and self.request.method == 'POST' and
            self.request.POST.get('inform_person') and
            self.request.POST['inform_person'] == 'on'):
            try:
                lgc_send_email(self.object.user, lgc_types.MsgType.DEL)
            except Exception as e:
                messages.error(self.request, _('Cannot send email to') + '`'
                               + self.object.user.email + '`: ' + str(e))
                return redirect('lgc-file', self.object.id)

        messages.success(self.request, success_message)
        return super().delete(request, *args, **kwargs)

@login_required
def ajax_person_process_search_view(request, *args, **kwargs):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    pk = kwargs.get('pk', '')
    objects = lgc_models.PersonProcess.objects.filter(person=pk).filter(active=False)
    term = request.GET.get('term', '')
    objs = objects.filter(process__name__istartswith=term)
    objs = objs[:10]

    col_list = ['name']
    col_list = set_bold_search_attrs(objs, col_list, term)
    context = {
        'objects': objs,
        'col_list': col_list,
    }
    return render(request, 'lgc/generic_search.html', context)

@login_required
def __ajax_process_stage_search_view(request, model):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    term = request.GET.get('term', '')
    if translation.get_language() == 'fr':
        objs = model.objects.filter(name_fr__istartswith=term)
        col_list = ['name_fr']
    else:
        objs = model.objects.filter(name_en__istartswith=term)
        col_list = ['name_en']
    objs = objs[:10]

    context = {
        'objects': objs,
        'col_list': col_list,
    }
    return render(request, 'lgc/generic_search.html', context)

def ajax_process_stage_search_view(request):
    return __ajax_process_stage_search_view(request, lgc_models.ProcessStage)
def ajax_process_search_view(request):
    return __ajax_process_stage_search_view(request, lgc_models.Process)

class ProcessCommonView(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        if self.request.user.role not in user_models.get_internal_roles():
            return False
        return True

    def get_ordered_stages(self, process):
        if process == None or len(process.stages.all()) == 0:
            return None
        process_stages = process.stages
        all_process_stages = lgc_models.ProcessStage.objects
        objects = []

        for s in process_stages.through.objects.filter(process_id=process.id).order_by('id').all():
            objects.append(all_process_stages.filter(id=s.processstage_id)[0])
        return objects

    def get_available_stages(self, selected_stages):
        available_stages = []
        for s in lgc_models.ProcessStage.objects.all():
            if selected_stages == None:
                available_stages.append(s)
                continue
            present = False
            for s_selected in selected_stages.all():
                if s.id == s_selected.id:
                    present = True
                    break
            if present == False:
                available_stages.append(s)
        return available_stages

    def form_valid(self, form):
        if self.model != lgc_models.Process:
            return super().form_valid(form)

        """Always save the stages. This will keep their order."""
        with transaction.atomic():
            if self.object:
                form.instance.stages.clear()
            form.instance.save()
            for s in form.data.getlist('stages'):
                form.instance.stages.add(s)
        return super().form_valid(form)

    class Meta:
        abstract = True

class ProcessListView(ProcessCommonView, ListView):
    template_name = 'lgc/sub_generic_list.html'
    model = lgc_models.Process
    title = _('Processes')
    create_url = reverse_lazy('lgc-process-create')
    item_url = 'lgc-process'
    this_url = reverse_lazy('lgc-processes')
    ajax_search_url = reverse_lazy('lgc-process-search-ajax')
    search_url = reverse_lazy('lgc-processes')

    def get_queryset(self):
        term = self.request.GET.get('term', '')
        order_by = self.get_ordering()
        if term == '':
            return self.model.objects.order_by(order_by)
        objs = (self.model.objects.filter(name_fr__istartswith=term)|
                self.model.objects.filter(name_en__istartswith=term))
        return objs.order_by(order_by)

    def get_ordering(self):
        order_by = self.request.GET.get('order_by', 'id')
        if order_by == 'name':
            if translation.get_language() == 'fr':
                return 'name_fr'
            return 'name_en'
        if order_by == '-name':
            if translation.get_language() == 'fr':
                return '-name_fr'
            return '-name_en'

        return order_by

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['create_url'] = self.create_url
        context['item_url'] = self.item_url
        context['ajax_search_url'] = self.ajax_search_url
        context['search_url'] = self.search_url
        context['header_values'] = [('ID', 'id'), (_('Name'), 'name')]

        lang = translation.get_language()
        for obj in context['object_list']:
            if lang == 'fr':
                obj.name = obj.name_fr
            else:
                obj.name = obj.name_en

        return pagination(self.request, context, self.this_url)

class ProcessCreateView(ProcessCommonView, SuccessMessageMixin, CreateView):
    model = lgc_models.Process
    success_message = _('Process successfully created')
    template_name = 'lgc/process.html'
    success_url = reverse_lazy('lgc-process-create')
    title = _('New Process')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        if self.model == lgc_models.Process:
            context['available_stages'] = lgc_models.ProcessStage.objects.all()
        return context

    def test_func(self):
        return self.request.user.is_staff

    def get_form(self, form_class=lgc_forms.ProcessForm):
        return super().get_form(form_class=form_class)

class ProcessUpdateView(ProcessCommonView, SuccessMessageMixin, UpdateView):
    model = lgc_models.Process
    success_message = _('Process successfully updated')
    success_url = 'lgc-process'
    template_name = 'lgc/process.html'
    title = _('Process')
    delete_url = 'lgc-process-delete'
    fields = '__all__'

    def get_success_url(self):
        self.object = self.get_object()
        return reverse_lazy(self.success_url, kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        if self.delete_url != '':
            context['delete_url'] = reverse_lazy(self.delete_url,
                                                 kwargs={'pk':self.object.id})
        if self.model == lgc_models.Process:
            context['available_stages'] = self.get_available_stages(self.object.stages)
            context['stages'] = self.get_ordered_stages(self.object)
        return context

    def test_func(self):
        return self.request.user.is_staff

class ProcessDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = lgc_models.Process
    template_name = 'lgc/process_confirm_delete.html'
    success_url = reverse_lazy('lgc-processes')
    title = _('Delete Process')
    cancel_url = 'lgc-process'
    obj_name = _('Process')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['cancel_url'] = reverse_lazy(self.cancel_url,
                                             kwargs={'pk':self.object.id})
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_message = (_("%(obj_name)s %(id)s successfully deleted."%
                           {'obj_name': self.obj_name,
                            'id': self.object.id}))
        messages.success(self.request, success_message)
        return super().delete(request, *args, **kwargs)

class ProcessStageListView(ProcessListView):
    model = lgc_models.ProcessStage
    title = _('Process Stages')
    create_url = reverse_lazy('lgc-process-stage-create')
    item_url = 'lgc-process-stage'
    this_url = reverse_lazy('lgc-process-stages')
    ajax_search_url = reverse_lazy('lgc-process-stage-search-ajax')
    search_url = reverse_lazy('lgc-process-stages')

class ProcessStageCreateView(ProcessCreateView):
    model = lgc_models.ProcessStage
    success_message = _('Process stage successfully created')
    success_url = reverse_lazy('lgc-process-stage-create')
    title = _('New Process Stage')
    template_name = 'lgc/generic_form.html'

    def get_form(self, form_class=lgc_forms.ProcessStageForm):
        return super().get_form(form_class=form_class)

class ProcessStageUpdateView(ProcessUpdateView):
    model = lgc_models.ProcessStage
    success_message = _('Process stage successfully updated')
    success_url = 'lgc-process-stage'
    title = _('Process Stage')
    delete_url = 'lgc-process-stage-delete'
    template_name = 'lgc/generic_form.html'

    def get_form(self, form_class=lgc_forms.ProcessStageForm):
        return super().get_form(form_class=form_class)

class ProcessStageDeleteView(ProcessDeleteView):
    model = lgc_models.ProcessStage
    success_url = reverse_lazy('lgc-process-stages')
    title = _('Delete Process Stage')
    cancel_url = 'lgc-process-stage'
    obj_name = _('Process stage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = translation.get_language()
        return context

class PersonProcessUpdateView(LoginRequiredMixin, UserPassesTestMixin,
                              SuccessMessageMixin, UpdateView):
    model = lgc_models.PersonProcess
    template_name = 'lgc/person_process.html'
    success_message = _('Process successfully updated.')
    success_url = 'lgc-person-process'
    delete_url = ''
    fields = '__all__'

    def test_func(self):
        return self.request.user.role in user_models.get_internal_roles()

    def is_process_complete(self):
        person_process_stages = self.object.stages.filter(is_specific=False)
        process_stages = self.object.process.stages.all()
        return len(process_stages) == len(person_process_stages.all())

    def get_stage_forms(self):
        if self.is_process_complete():
            stage_form = lgc_forms.UnboundFinalPersonProcessStageForm
        else:
            stage_form = lgc_forms.UnboundPersonProcessStageForm
        if self.request.POST:
            stage_form = stage_form(self.request.POST)
            specific_form = lgc_forms.PersonProcessSpecificStageForm(self.request.POST)
        else:
            stage_form = stage_form()
            specific_form = lgc_forms.PersonProcessSpecificStageForm()
        stage_form.helper = FormHelper()
        stage_form.helper.form_tag = False
        stage_form.helper.layout = Layout(
            Div(Div('action', css_class='form-group col-md-3'),
                css_class='form-row'),
        )
        return specific_form, stage_form

    def get_success_url(self):
        return reverse_lazy(self.success_url, kwargs={'pk': self.object.id})

    def get_formset(self):
        stagesFormSet = modelformset_factory(lgc_models.PersonProcessStage,
                                             form=lgc_forms.PersonProcessStageForm,
                                             can_delete=False, extra=0)

        if self.request.POST:
            formset = stagesFormSet(self.request.POST)
        else:
            formset = stagesFormSet(queryset=self.object.stages.order_by('id'))
        for form in formset:
            if translation.get_language() == 'fr':
                name = 'name_fr'
            else:
                name = 'name_en'
            form.helper = FormHelper()
            form.helper.form_tag = False
            form.fields[name].label = _('Stage Name')
            form.fields[name].widget.attrs['disabled'] = True
            if not self.object.active:
                form.fields['validation_date'].widget.attrs['disabled'] = True
                form.fields['stage_comments'].widget.attrs['disabled'] = True
            form.helper.layout = Layout(
                Div(
                    Div('id'), Div(name, css_class='form-group col-md-2'),
                    Div('validation_date', css_class='form-group col-md-2'),
                    Div('stage_comments', css_class='form-group col-md-3'),
                    css_class='form-row'),
            )

        return formset

    def get_context_data(self, **kwargs):
        person_common = PersonCommonView()
        context = super().get_context_data(**kwargs)
        if translation.get_language() == 'fr':
            name = self.object.name_fr
        else:
            name = self.object.name_en
        context['title'] = _('Process') + ' ' + name

        self.object.form = lgc_forms.PersonProcessForm(instance=self.object)
        context['timeline_stages'] = person_common.get_timeline_stages(self.object)
        specific_stage, stage_form = self.get_stage_forms()
        if self.object.active:
            context['specific_stage'] = specific_stage
            context['stage_form'] = stage_form
        else:
            context['go_back'] = self.request.META.get('HTTP_REFERER')

        context['formset'] = self.get_formset()
        return context

    def get_form(self, form_class=lgc_forms.PersonProcessCompleteForm):
        form = super().get_form(form_class=form_class)
        form.helper = FormHelper()
        form.helper.form_tag = False
        form.helper.layout = Layout(
            Div(
                Div('consulate', css_class='form-group col-md-2'),
                Div('prefecture', css_class='form-group col-md-2'),
                css_class='form-row'),
            Div(
                Div('no_billing', css_class='form-group col-md-4'),
                css_class='form-row'),
            )
        if not self.object.active:
            form.fields['no_billing'].widget.attrs['disabled'] = True
            form.fields['consulate'].widget.attrs['disabled'] = True
            form.fields['prefecture'].widget.attrs['disabled'] = True
        elif hasattr(self.object, 'invoice') and self.object.invoice:
            form.fields['no_billing'].widget.attrs['disabled'] = True

        return form

    def get_last_person_process_stage(self, stages):
        if stages == None or stages.count() == 0:
            return None
        return stages.all()[stages.all().count()-1]

    def generate_next_person_process_stage(self, person_process,
                                           name_fr, name_en,
                                           is_specific=False):
        next_stage = lgc_models.PersonProcessStage()
        next_stage.is_specific = is_specific
        next_stage.person_process = person_process
        next_stage.start_date = str(datetime.date.today())
        next_stage.name_fr = name_fr
        next_stage.name_en = name_en
        next_stage.validation_date = timezone.now()
        next_stage.save()

    def get_next_process_stage(self, person_process_stages, process):
        process_common = ProcessCommonView()
        process_stages = process_common.get_ordered_stages(process)

        if person_process_stages == None:
            if process_stages == None or len(process_stages) == 0:
                return None
            return process_stages[0]
        person_process_stages = person_process_stages.filter(is_specific=False)
        if (person_process_stages == None or
            person_process_stages.count() == 0):
            return process_stages[0]

        last_pos = person_process_stages.count() - 1
        length = len(process_stages)
        pos = 0
        for s in process_stages:
            if pos < last_pos:
                pos += 1
                continue
            if pos == length:
                return process_stages[pos]
            try:
                return process_stages[pos + 1]
            except:
                return None
        return None

    def get_previous_process_stage(self, process_stages, process_stage):
        if process_stage == None or len(process_stages.all()) == 1:
            return process_stages.first()
        process_stages = process_stages.all()

        length = len(process_stages)
        pos = 0
        for s in process_stages:
            if s.id != process_stage.id:
                pos += 1
                continue
            if pos == length:
                return process_stages[pos - 1]
        return None

    def form_valid(self, form):
        if (form.cleaned_data['no_billing'] and
            hasattr(self.object, 'invoice') and self.object.invoice):
            messages.error(self.request, _('This process has already an invoice'))
            return super().form_invalid(form)

        specific_stage_form, stage_form = self.get_stage_forms()
        if not specific_stage_form.is_valid() or not stage_form.is_valid():
            messages.error(self.request, _('Invalid form'))
            return super().form_invalid(form)

        formset = self.get_formset()
        if not formset.is_valid():
            messages.error(self.request, _('Invalid stages form:'))
            return super().form_invalid(form)

        for sform in formset:
            sform.save()

        action = stage_form.cleaned_data.get('action')
        if action == lgc_forms.PROCESS_STAGE_VALIDATE:
            next_process_stage = self.get_next_process_stage(self.object.stages,
                                                             self.object.process)
            if next_process_stage != None:
                self.generate_next_person_process_stage(self.object,
                                                        next_process_stage.name_fr,
                                                        next_process_stage.name_en)
            else:
                messages.error(self.request, _('The next stage does not exist.'))
                return super().form_invalid(form)
        elif action == lgc_forms.PROCESS_STAGE_DELETE:
            last_stage = self.get_last_person_process_stage(self.object.stages)
            if last_stage == None:
                messages.error(self.request, _('This process has no validated stages.'))
                return super().form_invalid(form)
            last_stage.delete()
        elif action == lgc_forms.PROCESS_STAGE_ADD_SPECIFIC:
            if (specific_stage_form.cleaned_data['name_fr'] == '' or
                specific_stage_form.cleaned_data['name_en'] == ''):
                messages.error(self.request, _('The specific stage names are invalid.'))
                return super().form_invalid(form)

            self.generate_next_person_process_stage(self.object,
                                                    specific_stage_form.cleaned_data['name_fr'],
                                                    specific_stage_form.cleaned_data['name_en'],
                                                    is_specific=True)

        elif action == lgc_forms.PROCESS_STAGE_COMPLETED:
            if not self.is_process_complete():
                messages.error(self.request, _('The process is not complete.'))
                return super().form_invalid(form)
            form.instance.active = False
            super().form_valid(form)
            return redirect('lgc-file', self.object.person.id)

        return super().form_valid(form)

class PersonProcessListView(ProcessListView):
    model = lgc_models.PersonProcess
    create_url = ''
    item_url = 'lgc-person-process'

    def get_ordering(self):
        order_by = self.request.GET.get('order_by', 'id')
        if order_by == 'name':
            return 'process__name'
        if order_by == '-name':
            return '-process__name'

        return order_by

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if translation.get_language() == 'fr':
            name = 'name_fr'
        else:
            name = 'name_en'
        for obj in context['object_list']:
            obj.name = getattr(obj.process, name)
        return context

    def get_queryset(self, *args, **kwargs):
        pk = self.kwargs.get('pk', '')
        object_list = lgc_models.PersonProcess.objects.filter(person=pk).filter(active=False)
        if object_list == None or object_list.count() == 0:
            raise Http404
        self.ajax_search_url = reverse_lazy('lgc-person-process-search-ajax',
                                            kwargs={'pk':pk})
        self.search_url = reverse_lazy('lgc-person-processes',
                                       kwargs={'pk':pk})
        person = object_list[0].person
        self.title = (_('Completed Processes of %(first_name)s %(last_name)s'%
                      {'first_name': person.first_name,
                       'last_name': person.last_name}))

        term = self.request.GET.get('term', '')
        order_by = self.get_ordering()
        if term == '':
            return object_list.order_by(order_by)
        return object_list.filter(process__name__istartswith=term).order_by(order_by)

def get_account_layout(layout, new_token, is_hr=False, is_active=False):
    div = Div(css_class='form-row');
    if is_hr:
        layout.append(Div('active_tab'))

    layout.append(
        Div(
            Div('first_name', css_class='form-group col-md-4'),
            Div('last_name', css_class='form-group col-md-4'),
            css_class='form-row'))
    layout.append(
        Div(
            Div('email', css_class='form-group col-md-4'),
            Div('language', css_class='form-group col-md-4'),
            css_class='form-row'))
    if is_hr:
        div.append(Div('company', css_class='form-group col-md-4'));
    div.append(Div('responsible', css_class='form-group col-md-4'));
    layout.append(div)

    if is_active:
        row_div = Div(css_class='form-row')
        row_div.append(Div('is_active', css_class='form-group col-md-4'))
        layout.append(row_div)
        row_div = Div(css_class='form-row')
        row_div.append(Div('status', css_class='form-group col-md-4'))
        layout.append(row_div)

    if new_token or is_hr:
        row_div = Div(css_class='form-row')
        if new_token:
            row_div.append(Div('new_token', css_class='form-group col-md-4'))
        if is_hr:
            row_div.append(Div('is_admin', css_class='form-group col-md-4'))
        layout.append(row_div)


    return layout

def get_account_form(form, action, uid, is_staff=False, new_token=False):
    form.helper = FormHelper()
    form.helper.layout = get_account_layout(Layout(), new_token, is_hr=False,
                                            is_active=uid)

    form.helper.layout.append(
        HTML('<button class="btn btn-outline-info" type="submit">' +
             action + '</button>'))
    if uid and is_staff:
        form.helper.layout.append(
            HTML(' <a href="{% url "lgc-account-delete" ' + str(uid) +
                 '%}" class="btn btn-outline-danger">' + delete_str + '</a>')
        )
    return form

def get_hr_account_form(form, action, uid, new_token=False):
    form.helper = FormHelper()
    if uid:
        form.helper.layout = Layout(TabHolder(
            LgcTab(_('Information'), get_account_layout(Layout(), new_token,
                                                        is_hr=True, is_active=True)),
            LgcTab(_('Employees'),
                Div(Div(HTML(get_template(CURRENT_DIR, 'lgc/employee_list.html')),
                        css_class="form-group col-md-10"),
                    css_class="form-row")),
        ))
    else:
        form.helper.layout = get_account_layout(Layout(), new_token, is_hr=True)

    form.helper.layout.append(
        HTML('<button class="btn btn-outline-info" type="submit">' +
             action + '</button>'))
    if uid:
        form.helper.layout.append(
            HTML(' <a href="{% url "lgc-hr-delete" ' + str(uid) +
                 '%}" class="btn btn-outline-danger">' + delete_str + '</a>')
        )

    return form

class AccountView(LoginRequiredMixin, UserPassesTestMixin):
    template_name = 'lgc/generic_form_with_formsets.html'
    model = User
    success_url = 'lgc-account'
    delete_url = 'lgc-account-delete'
    create_url = reverse_lazy('lgc-account-create')
    update_url = 'lgc-account'
    cancel_url = 'lgc-account'
    list_url = reverse_lazy('lgc-accounts')
    form_class = lgc_forms.InitiateAccountForm
    is_hr = False

    class Meta:
        abstract = True

    def test_func(self):
        return self.request.user.role in user_models.get_internal_roles()

class InitiateAccount(AccountView, SuccessMessageMixin, CreateView):
    success_message = _('New account successfully initiated')
    title = _('Initiate an account')
    form_name = _('Initiate account')

    def test_func(self):
        return self.request.user.role in user_models.get_internal_roles()

    def get_success_url(self):
        return reverse_lazy(self.success_url, kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        if not self.is_hr:
            try:
                p = self.get_person()
                context['form'].fields['first_name'].initial = p.first_name
                context['form'].fields['last_name'].initial = p.last_name
                context['form'].fields['email'].initial = p.email
            except:
                pass

        return context

    def get_form(self, form_class=lgc_forms.InitiateAccountForm):
        form = super().get_form(form_class=self.form_class)

        if self.is_hr:
            return get_hr_account_form(form, self.form_name, None,
                                       new_token=True)
        return get_account_form(form, self.form_name, None, new_token=True)

    def return_non_existant(self, form, pk):
        messages.error(self.request,
                       _("Cannot link with a non-existent file `%s'"%pk))
        return super().form_invalid(form)

    def get_person(self):
        pk = self.kwargs.get('pk', '')
        if pk != '':
            p = lgc_models.Person.objects.filter(id=pk)
            if p == None or len(p) == 0:
                raise ValueError('invalid person ID')
            return p.get()
        return None

    def form_valid(self, form):
        try:
            p = self.get_person()
        except:
            return self.return_non_existant(form, self.kwargs.get('pk', ''))

        self.object = form.save(commit=False)
        form.instance.is_active = True

        if self.is_hr:
            if form.cleaned_data['is_admin']:
                form.instance.role = user_models.HR_ADMIN
            else:
                form.instance.role = user_models.HR
        else:
            form.instance.role = user_models.EMPLOYEE
        if form.cleaned_data['new_token']:
            form.instance.token = token_generator()
            form.instance.token_date = timezone.now()
            if self.is_hr:
                type = lgc_types.MsgType.NEW_HR
            else:
                type = lgc_types.MsgType.NEW_EM
            try:
                lgc_send_email(self.object, type)
            except Exception as e:
                messages.error(self.request, _('Cannot send email to') + '`'
                               + self.object.email + '`: ' + str(e))
                return super().form_invalid(form)
        ret = super().form_valid(form)
        self.object = form.save()
        if p:
            p.user = self.object
            p.email = self.object.email
            p.first_name = self.object.first_name
            p.last_name = self.object.last_name
            p.save()
        return ret

    def form_invalid(self, form):
        messages.error(self.request, _('There are errors on the page'))
        return super().form_invalid(form)

class Accounts(AccountView, PersonCommonListView, UserPassesTestMixin):
    title = _('Employee Accounts')
    template_name = 'lgc/accounts.html'
    ajax_search_url = reverse_lazy('user-employee-search-ajax')
    search_url = reverse_lazy('lgc-accounts')
    users = user_models.get_employee_user_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['create_url'] = self.create_url
        context['update_url'] = self.update_url
        context['show_status'] = True

        return pagination(self.request, context, self.list_url)

    def get_queryset(self):
        term = self.request.GET.get('term', '')
        options = self.request.GET.get('options', '')
        if options == 'pending':
            users = self.users.filter(status=user_models.USER_STATUS_PENDING)
        elif options == 'deleted':
            users = self.users.filter(status__in=user_models.get_user_deleted_statuses())
        else:
            users = self.users
        order_by = self.get_ordering()
        if term == '':
            return users.order_by(order_by)
        objs = (users.filter(email__istartswith=term)|
                users.filter(first_name__istartswith=term)|
                users.filter(last_name__istartswith=term))
        return objs.order_by(order_by)

class UpdateAccount(AccountView, SuccessMessageMixin, UpdateView):
    success_message = _('Account successfully updated')
    title = _('Update Account')
    form_name = _('Update')
    is_hr = False

    def get_success_url(self):
        return reverse_lazy(self.success_url, kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['formset_title'] = _('Employees')
        context['formset_add_text'] = _('Add an employee')
        if self.is_hr and self.object.role == user_models.HR_ADMIN:
            context['form'].fields['is_admin'].initial = True
        context['form'].fields['new_token'].initial = False
        del context['user']
        if self.object and hasattr(self.object, 'person_user_set'):
            context['file_url'] = reverse_lazy('lgc-file', kwargs={'pk':self.object.person_user_set.id})
        return context

    def get_form(self, form_class=lgc_forms.InitiateAccountForm):
        form = super().get_form(form_class=self.form_class)

        if self.is_hr:
            return get_hr_account_form(form, self.form_name, self.object.id,
                                       new_token=True)
        return get_account_form(form, self.form_name, self.object.id,
                                is_staff=self.request.user.is_staff,
                                new_token=True)

    def form_valid(self, form, relations = None):
        pending_user_err_msg = _('The status cannot be set to active as ' +
                                 'the user has not accepted our terms and ' +
                                 'condiftions yet.')

        user = User.objects.filter(id=self.object.id)
        if len(user) != 1:
            return self.form_invalid(form)
        user = user[0]

        if (user.status == user_models.USER_STATUS_PENDING and
            form.cleaned_data['status'] == user_models.USER_STATUS_ACTIVE):
            messages.error(self.request, pending_user_err_msg)
            return redirect('lgc-account', self.object.id)

        if (user.status not in user_models.get_user_deleted_statuses() and
            form.cleaned_data['status'] in user_models.get_user_deleted_statuses()):
            messages.error(self.request, _('Deleted status cannot be set.'))
            form.cleaned_data['status'] = user.status
            return redirect('lgc-account', self.object.id)

        self.object = form.save(commit=False)

        if hasattr(self.object, 'person_user_set'):
            self.object.person_user_set.first_name = self.object.first_name
            self.object.person_user_set.last_name = self.object.last_name
            self.object.person_user_set.email = self.object.email
            self.object.person_user_set.responsible.set(form.instance.responsible.all())
            self.object.person_user_set.save()
        elif (self.object.status == user_models.USER_STATUS_ACTIVE and
              self.object.role == user_models.EMPLOYEE):
            messages.error(self.request, pending_user_err_msg)
            return redirect('lgc-account', self.object.id)

        if self.is_hr:
            if form.cleaned_data['is_admin']:
                form.instance.role = user_models.HR_ADMIN
            else:
                form.instance.role = user_models.HR
        else:
            form.instance.role = user_models.EMPLOYEE

        if form.cleaned_data['new_token']:
            form.instance.token = token_generator()
            form.instance.token_date = timezone.now()
            form.instance.password = ''
            if self.is_hr:
                type = lgc_types.MsgType.NEW_HR
            else:
                type = lgc_types.MsgType.NEW_EM
            try:
                lgc_send_email(self.object, type)
            except Exception as e:
                messages.error(self.request, _('Cannot send email to') + '`'
                               + self.object.email + '`: ' + str(e))
                return super().form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('There are errors on the page'))
        return super().form_invalid(form)

class DeleteAccount(AccountView, PersonDeleteView):
    obj_name = _('Account')
    title = _('Delete Account')
    success_url = reverse_lazy('lgc-accounts')
    template_name = 'lgc/person_confirm_delete.html'

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not hasattr(self.object, 'person_user_set'):
            return super().delete()
        if not hasattr(self.object.person_user_set, 'document_set'):
            return super().delete()

        for doc in self.object.person_user_set.document_set.all():
            try:
                lgc_models.delete_doc(self.object.person_user_set, doc)
            except Exception as e:
                print(e)
                messages.error(self.request, _('Cannot remove user files.'))
                return redirect('lgc-account', self.object.id)

        return super().delete()

class HRView(LoginRequiredMixin):
    req_type = lgc_types.ReqType.HR
    template_name = 'lgc/generic_form_with_formsets.html'
    model = User
    success_url = 'lgc-hr'
    delete_url = 'lgc-hr-delete'
    create_url = reverse_lazy('lgc-hr-create')
    update_url = 'lgc-hr'
    cancel_url = 'lgc-hr'
    list_url = reverse_lazy('lgc-hr-accounts')
    form_class = lgc_forms.InitiateHRForm
    is_hr = True

    class Meta:
        abstract = True

    def test_func(self):
        return self.request.user.role in user_models.get_internal_roles()

class HRCreateView(HRView, InitiateAccount):
    success_message = _('New HR account successfully initiated')
    title = _('New HR account')
    form_name = _('Initiate account')

    def test_func(self):
        return (self.request.user.role == user_models.CONSULTANT or
                self.request.user.is_staff)

class HRUpdateView(HRView, UpdateAccount, UserPassesTestMixin):
    success_message = _('HR account successfully updated')
    title = _('Update HR')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset_title'] = ''
        context['formset_add_text'] = _('Add an employee')
        EmployeeFormSet = formset_factory(lgc_forms.HREmployeeForm,
                                          extra=0, can_delete=True)

        set_active_tab(self, context)
        if self.request.POST:
            context['formset'] = EmployeeFormSet(self.request.POST)
        else:
            init = []
            for p in self.object.hr_employees.all():
                if p.role != user_models.EMPLOYEE:
                    continue;
                init.append({'id':p.id,
                             'first_name':p.first_name,
                             'last_name':p.last_name,
                             'email':p.email,
                })
            context['formset'] = EmployeeFormSet(initial=init)

        return context

    def is_deleted(self, employees, id):
        for e in employees.deleted_forms:
            if e.cleaned_data['id'] == id:
                return True
        return False

    def form_valid(self, form):
        context = self.get_context_data()
        employees = context['formset']
        save_active_tab(self)

        if not self.request.POST:
            return super().form_valid(form)

        if not form.is_valid():
            return super().form_invalid(form)

        if not employees.is_valid():
            messages.error(self.request, _('Invalid Employee table'))
            return super().form_invalid(form)

        self.object = form.save()
        self.object.hr_employees.clear()

        users = user_models.get_employee_user_queryset()
        for e in employees.cleaned_data:
            if not 'id' in e:
                continue
            if self.is_deleted(employees, e['id']):
                continue
            u = users.filter(id=e['id'])
            if u == None or len(u) == 0:
                messages.error(self.request, _("Unknown employee ID `%s'"%(e['id'])))
                return super().form_invalid(form)
            u = u.get()
            if u == None:
                messages.error(self.request, _("Unknown employee ID `%s'"%(e['id'])))
                return super().form_invalid(form)
            if u.email == None:
                messages.error(self.request, _("Employee's e-mail cannot be empty"))
                return super().form_invalid(form)
            self.object.hr_employees.add(u)
        self.object.save()
        return super().form_valid(form, self.object.hr_employees.all())

class HRAccountListView(HRView, Accounts):
    title = _('HR accounts')
    template_name = 'lgc/accounts.html'
    ajax_search_url = reverse_lazy('user-hr-search-ajax')
    search_url = reverse_lazy('lgc-hr-accounts')
    users = user_models.get_hr_user_queryset()

class HRDeleteView(HRView, DeleteAccount):
    success_url = reverse_lazy('lgc-hr-accounts')
    obj_name = _('HR account')
    title = _('Delete HR account')
    template_name = 'lgc/person_confirm_delete.html'

@login_required
def settings_view(request):
    if not request.user.billing:
        raise Http404

    if request.method == 'POST':
        form = lgc_forms.SettingsForm(request.POST)
        if form.is_valid():
            settings = form.save(commit=False)
            settings.rate_eur = 1
            settings.id = 1
            settings.save()
            messages.success(request, _('Settings successfully updated'))
        else:
            messages.error(request, _('Cannot save'))
    else:
        slen = lgc_models.Settings.objects.count()
        print('slen:', slen)
        if slen == 0:
            settings = lgc_models.Settings()
            settings.rate_eur = 1
            settings.save()
        elif slen == 1:
            settings = lgc_models.Settings.objects.all()[0]
        else:
            return HttpResponse(status=500)
        form = lgc_forms.SettingsForm(instance=settings)
    form.helper = FormHelper()
    form.helper.layout = Layout(
        Div(
            Div(HTML('<label>' + _('Currencies') + '</label>'),
                css_class='form-group col-md-1'),
            css_class='form-row'),
        Div(
            Div('rate_eur', css_class='form-group col-md-1 bg-info'),
            Div('rate_usd', css_class='form-group col-md-1'),
            Div('rate_cad', css_class='form-group col-md-1'),
            Div('rate_gbp', css_class='form-group col-md-1'),
            css_class='form-row'),
        HTML('<button class="btn btn-outline-info" type="submit">' +
        _('Update') + '</button>'))
    form.fields['rate_eur'].widget.attrs['readonly'] = True

    context = {
        'title': _('Settings'),
        'form': form,
    }
    return render(request, 'lgc/generic_form_with_formsets.html', context)

@login_required
@must_be_staff
def ajax_insert_employee_view(request):
    term = request.GET.get('term', '')
    users = user_models.get_employee_user_queryset()
    employees = users.filter(first_name__istartswith=term)|users.filter(last_name__istartswith=term)|users.filter(email__istartswith=term)
    employees = employees[:10]

    set_bold_search_attrs(employees, ['first_name', 'last_name', 'email'], term)
    context = {
        'employees': employees
    }
    return render(request, 'lgc/insert_employee.html', context)

def ajax_file_search_find_objs(objs, term):
    return (objs.filter(first_name__istartswith=term)|
            objs.filter(last_name__istartswith=term)|
            objs.filter(email__istartswith=term)|
            objs.filter(host_entity__istartswith=term)|
            objs.filter(home_entity__istartswith=term))

@login_required
def ajax_file_search_view(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    if request.user.role == user_models.JURIST:
        objs = lgc_models.Person.objects.filter(responsible=request.user)
    else:
        objs = lgc_models.Person.objects

    all_objs = []
    term = request.GET.get('term', '')

    """ ignore empty requests """
    if term == '':
        return

    if term == 'le' or term == 'la':
        eterm = term + ' '
        efiles = ajax_file_search_find_objs(objs, eterm)[:10]
        if len(efiles) < 10:
            files = objs.exclude(first_name__istartswith=eterm).exclude(last_name__istartswith=eterm).exclude(email__istartswith=eterm).exclude(host_entity__istartswith=eterm).exclude(home_entity__istartswith=eterm)
            files = ajax_file_search_find_objs(files, term)[:(10-len(efiles))]
        else:
            files = None
    else:
        efiles = None
        files = ajax_file_search_find_objs(objs, term)[:10]

    if efiles:
        for obj in efiles:
            all_objs.append(obj)
    for obj in files:
        all_objs.append(obj)

    col_list = ['first_name', 'last_name', 'email', 'host_entity', 'home_entity']
    col_list = set_bold_search_attrs(all_objs, col_list, term)

    context = {
        'objects': all_objs,
        'col_list': col_list,
    }
    return render(request, 'lgc/generic_search.html', context)

@login_required
def download_file(request, *args, **kwargs):
    pk = kwargs.get('pk', '')
    doc = lgc_models.Document.objects.filter(id=pk).all()
    if doc == None or len(doc) != 1:
        raise Http404

    if (request.user.role not in user_models.get_internal_roles() and
        doc.person.user.id != request.user.id):
        return http.HttpResponseForbidden()

    file_path = os.path.join(settings.MEDIA_ROOT, doc[0].document.name)
    if not os.path.exists(file_path):
        raise Http404
    with open(file_path, 'rb') as fh:
        res = http.HttpResponse(fh.read(), content_type='application/octet-stream')
        res['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
        return res
    raise Http404

def paginate_expirations(request, object_list):
    paginate = request.GET.get('paginate', 10)
    order_by = request.GET.get('order_by', 'end_date')
    object_list = object_list.order_by(order_by)
    paginator = Paginator(object_list, paginate)
    page = request.GET.get('page')
    return paginator.get_page(page)

def expirations_filter_objs(request, objs):
    expires = request.GET.get('expires', None)
    expiry_type = request.GET.get('expiry_type', None)
    show_disabled = request.GET.get('show_disabled', None)
    dont_show_expired = request.GET.get('dont_show_expired', None)

    """ initial value of 'expires' must be set """
    if expires == None:
        request.GET = request.GET.copy()
        request.GET['expires'] = settings.EXPIRATIONS_NB_DAYS

    try:
        delta = datetime.timedelta(days=int(expires))
    except:
        delta = datetime.timedelta(days=settings.EXPIRATIONS_NB_DAYS)
    compare_date = timezone.now().date() + delta
    objs = objs.filter(end_date__lte=compare_date)

    if expiry_type:
        objs = objs.filter(type=expiry_type)
    if not show_disabled:
        objs = objs.filter(enabled=True)
    if dont_show_expired:
        objs = objs.exclude(end_date__lte=timezone.now().date())
    return objs

def get_expirations_form(request):
    if len(request.GET):
        form = lgc_forms.ExpirationSearchForm(request.GET)
    else:
        form = lgc_forms.ExpirationSearchForm()
        form.fields['expires'].initial = settings.EXPIRATIONS_NB_DAYS
    form.helper = FormHelper()
    form.helper.form_method = 'get'
    form.helper.layout = Layout(
        Div(
            Div('user', css_class='form-group col-md-2'),
            Div('expires', css_class='form-group col-md-2'),
            Div('expiry_type', css_class='form-group col-md-3'),
            Div('show_disabled', css_class='form-group col-md-2 lgc_aligned_checkbox'),
            Div('dont_show_expired', css_class='form-group col-md-3 lgc_aligned_checkbox'),
            css_class='form-row'),
    )
    return form

@login_required
def __expirations(request, form, objs):
    context = {
        'title': 'Expirations',
        'search_form': form,
    }
    context = pagination(request, context, reverse_lazy('lgc-expirations'), 'end_date')

    if objs:
        objs = expirations_filter_objs(request, objs)
        context['page_obj'] = paginate_expirations(request, objs)

        if context['page_obj'].has_next() or context['page_obj'].has_previous():
            context['is_paginated'] = True
    else:
        context['is_paginated'] = False

    return render(request, 'lgc/expirations.html', context)

@login_required
def expirations(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    form = get_expirations_form(request)
    objs = expirations_filter_objs(request, lgc_models.Expiration.objects)
    for obj in objs:
        if obj.type == lgc_models.EXPIRATION_TYPE_DCEM and len(obj.child_set.all()) == 0:
            print('id:', obj.id, 'type:', obj.type, 'child_set:', len(obj.child_set.all()), 'employee_child_set:', len(obj.employee_child_set.all()))
            print('fixed detached child expiration', obj.id)
            obj.delete()

    user = request.GET.get('user', None)
    if user:
        user = User.objects.filter(id=user)
        if len(user) != 1:
            raise Http404
        objs = objs.filter(person__responsible__in=user)

    return __expirations(request, form, objs)
