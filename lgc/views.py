import pdb                # pdb.set_trace()
from django.db import transaction
from django.forms import formset_factory, modelformset_factory
from common.utils import (pagination, lgc_send_email, must_be_staff,
                          set_bold_search_attrs, get_template)
import common.utils as utils
from common.session_cache import session_cache_add, session_cache_get, session_cache_del
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
from . import models as lgc_models
from . import forms as lgc_forms
from employee import forms as employee_forms
from employee import models as employee_models
from .forms import LgcTab, LgcRadio
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
from users import models as user_models, views as user_views
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.utils.safestring import mark_safe
from common import lgc_types
import string, random, datetime, os, logging

log = logging.getLogger('lgc')

contact_admin_str = ugettext_lazy('Please contact your administrator.')
delete_str = ugettext_lazy('Delete')

User = get_user_model()
CURRENT_DIR = Path(__file__).parent

def token_generator(pw_rst=False):
    size = 64
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits

    while True:
        r = ''.join(random.choice(chars) for _ in range(size))

        """set the token type in the 7th byte"""
        b = (ord(r[7]) & 0xFE) | pw_rst

        """allow only letters and numbers"""
        if b > 90 and b < 97 or b > 122:
            b -= 10
        elif b < 65:
            b += 10

        r = r[:6] + chr(b) + r[7:]

        if len(User.objects.filter(token=r)) == 0:
            return r

def is_token_pw_rst(token):
    if len(token) < 64:
        return False
    return ord(token[7]) & 1

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

    if request.user.role == user_models.ROLE_EMPLOYEE:
        return render(request, 'employee/home.html', context)

    if request.user.role in user_models.get_hr_roles():
        return render(request, 'hr/home.html', context)

    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    employees = user_models.get_employee_user_queryset().filter(status=user_models.USER_STATUS_PENDING).count()
    hrs = user_models.get_hr_user_queryset().filter(status=user_models.USER_STATUS_PENDING).count()
    files = lgc_models.Person.objects.count()
    context['nb_pending_employees'] = employees
    context['nb_pending_hrs'] = hrs
    context['nb_files'] = files
    compare_date = (timezone.now().date() +
                    datetime.timedelta(days=settings.EXPIRATIONS_NB_DAYS))
    expirations = lgc_models.Expiration.objects.filter(person__responsible=request.user, enabled=True, end_date__lte=compare_date).order_by('end_date').count()
    context['nb_expirations'] = expirations
    if request.user.billing:
        context['nb_ready_invoices'] = lgc_models.Invoice.objects.filter(state=lgc_models.INVOICE_STATE_TOBEDONE).count()
    return render(request, 'lgc/home.html', context)

@login_required
def tables(request):
    return render(request, 'lgc/tables.html', {'title':'Tables'})

def user_access_test(request, obj_user):
    if request.user.role in user_models.get_internal_roles():
        return True

    if obj_user == None:
        return False

    """Employee check"""
    if request.user.role == user_models.ROLE_EMPLOYEE:
        return obj_user == request.user

    """HR check"""
    if request.user.role in user_models.get_hr_roles():
        return obj_user in request.user.hr_employees.all()

    return False

class UserTest(UserPassesTestMixin):
    def test_func(self):
        try:
            self.object = self.get_object()
        except:
            return user_access_test(self.request, None)
        return user_access_test(self.request, self.object.user)

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
        context['header_values'] = [('id', 'ID', 'is_private',
                                     '<i>(' + str(_('private')) + ')</i>'),
                                    ('first_name', _('First Name')),
                                    ('last_name', _('Last Name')), ('email', 'E-mail'),
                                    ('home_entity', _('Home Entity')),
                                    ('host_entity', _('Host Entity')),
                                    ('creation_date', _('Created'))]

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
                log.error('cannot get person process')
                continue
            proc = qs[proc_idx]
            if translation.get_language() == 'fr':
                obj.proc = proc.name_fr
            else:
                obj.proc = proc.name_en

        context['header_values'] += [('proc', 'Process')]

        return p

    def test_func(self):
        return self.request.user.role in user_models.get_internal_roles()

class PersonListView(PersonCommonListView):
    def match_extra_terms(self, objs):
        id = self.request.GET.get('id')
        info_process = self.request.GET.get('info_process')
        state = self.request.GET.get('state')
        jurist = self.request.GET.get('jurist')
        consultant = self.request.GET.get('consultant')
        prefecture = self.request.GET.get('prefecture')
        subprefecture = self.request.GET.get('subprefecture')
        consulate = self.request.GET.get('consulate')
        direccte = self.request.GET.get('direccte')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        process_state = self.request.GET.get('process_state')
        home_entity = self.request.GET.get('home_entity')
        host_entity = self.request.GET.get('host_entity')
        first_name = self.request.GET.get('first_name')
        last_name = self.request.GET.get('last_name')

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
            try:
                o = User.objects.get(id=jurist)
                objs = objs.filter(responsible=o)
            except:
                pass
        if consultant:
            try:
                o = User.objects.get(id=consultant)
                objs = objs.filter(responsible=o)
            except:
                pass
        if prefecture:
            objs = objs.filter(prefecture__exact=prefecture)
        if subprefecture:
            objs = objs.filter(subprefecture__exact=subprefecture)
        if consulate:
            objs = objs.filter(consulate__exact=consulate)
        if direccte:
            objs = objs.filter(direccte__exact=direccte)

        if start_date and end_date:
            objs = objs.filter(start_date__range=[utils.parse_date(start_date),
                                                  utils.parse_date(end_date)])
        elif start_date:
            objs = objs.filter(start_date__gte=utils.parse_date(start_date))
        elif end_date:
            objs = objs.filter(start_date__lte=utils.parse_date(end_date))
        if home_entity:
            objs = objs.filter(home_entity__istartswith=home_entity)
        if host_entity:
            objs = objs.filter(host_entity__istartswith=host_entity)
        if first_name:
            objs = objs.filter(first_name__istartswith=first_name)
        if last_name:
            objs = objs.filter(last_name__istartswith=last_name)
        return objs

    def get_queryset(self):
        term = self.request.GET.get('term')
        order_by = self.get_ordering()
        objs = self.match_extra_terms(lgc_models.Person.objects)

        if term:
            objs = (objs.filter(email=term)|objs.filter(first_name=term)|
                    objs.filter(last_name=term))
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
                Div('last_name', css_class='form-group col-md-3'),
                Div('first_name', css_class='form-group col-md-3'),
                Div('home_entity', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(
                Div('host_entity', css_class='form-group col-md-3'),
                Div('prefecture', css_class='form-group col-md-3'),
                Div('subprefecture', css_class='form-group col-md-3'),
                Div('direccte', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(
                Div('consulate', css_class='form-group col-md-3'),
                Div('start_date', css_class='form-group col-md-3'),
                Div('end_date', css_class='form-group col-md-3'),
                Div('process_state', css_class='form-group col-md-3'),
                css_class='form-row'),
            Div(
                Div('info_process', css_class='form-group col-md-3'),
                Div('state', css_class='form-group col-md-3'),
                Div('consultant', css_class='form-group col-md-3'),
                Div('jurist', css_class='form-group col-md-3'),
                css_class='form-row'),
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = self.get_search_form()
        return context

def get_spouse_information_div(request, form):
    expand = 'false'
    show = ''

    for f in ('spouse_first_name', 'spouse_last_name', 'spouse_birth_date',
              'spouse_citizenship', 'spouse_passport_expiry',
              'spouse_passport_nationality', 'spouse_foreigner_id'):
        attr = getattr(form.instance, f)
        if f in form.errors or (attr != None and attr != ''):
            expand = 'true'
            show = ' show'
            break

    return Div(
        Div(
            Div(
                Div(
                    Div(
                        HTML('<h5 class="mb-0"><button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapse_spouse_accordion_id" aria-expanded="' + expand + '" aria-controls="collapse_spouse_accordion_id">' + str(_('Spouse information')) + '</button></h5>'),
                        css_class='card-header',
                        id='heading_spouse_accordion_id'),
                    HTML('<div class="collapse' + show + '" id="collapse_spouse_accordion_id" aria-labelledby="heading_spouse_accordion_id" data-parent="#spouse_accordion">'),
                    Div(
                        Div(Div('spouse_first_name', css_class='form-group col-md-3'),
                            Div('spouse_last_name', css_class='form-group col-md-3'),
                            Div('spouse_birth_date', css_class='form-group col-md-3'),
                            css_class='form-row'),
                        Div(Div('spouse_citizenship', css_class='form-group col-md-3'),
                            Div('spouse_passport_expiry', css_class='form-group col-md-3'),
                            Div('spouse_passport_nationality', css_class='form-group col-md-3'),
                            css_class='form-row'),
                        Div(Div('spouse_foreigner_id', css_class='form-group col-md-3'),
                            css_class='form-row'),
                        css_class='card-body'),
                    HTML('</div>'),
                    css_class='card', style="overflow:visible;"),
                css_class='accordion', id='spouse_accordion'),
            css_class='col-md-10'),
        css_class='form-row'
    )

def local_user_get_person_form_layout(request, form, action, obj,
                                      completed_processes):
    external_profile = None
    form.helper = FormHelper()
    form.helper.form_tag = False

    info_tab = LgcTab(
        _('Information'),
        Div(Div('is_private'), css_class='form-row'),
        Div(Div('active_tab'),
            Div('first_name', css_class='form-group col-md-3'),
            Div('last_name', css_class='form-group col-md-3'),
            Div('email', css_class='form-group col-md-3'),
            Div('version'),
            css_class='form-row'),
        Div(
            Div('citizenship', css_class='form-group col-md-3'),
            Div('foreigner_id', css_class='form-group col-md-3'),
            Div('birth_date', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('info_process', css_class='form-group col-md-3'),
            Div('responsible', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('passport_expiry', css_class='form-group col-md-3'),
            Div('passport_nationality', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('work_permit', css_class='form-group col-md-6'),
            css_class='form-row'),
        Div(Div(HTML('<hr>'), css_class='form-group col-md-9'),
            css_class='form-row'),
        Div(Div('home_entity', css_class='form-group col-md-3'),
            Div('host_entity', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('home_entity_address', css_class='form-group col-md-3'),
            Div('host_entity_address', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('local_address', css_class='form-group col-md-3'),
            Div('local_phone_number', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('foreign_address', css_class='form-group col-md-3'),
            Div('foreign_phone_number', css_class='form-group col-md-3'),
            Div('foreign_country', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('prefecture', css_class='form-group col-md-3'),
            Div('subprefecture', css_class='form-group col-md-3'),
            Div('direccte', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('consulate', css_class='form-group col-md-3'),
            css_class='form-row'),
        get_spouse_information_div(request, form),
    )

    info_tab.append(Div(Div(HTML(get_template(CURRENT_DIR,
                                              'lgc/formsets_template.html')),
                            css_class='form-group col-md-10'),
                        css_class='form-row'))
    info_tab.append(Div(Div('comments', css_class='form-group col-md-3'),
                        Div('state', css_class='form-group col-md-3'),
                        Div('start_date', css_class='form-group col-md-3'),
                        Div('today_date'),
                        css_class='form-row'))

    tab_holder = TabHolder(info_tab)

    if obj:
        external_profile = LgcTab(_('Account Profile'))
        if obj.user:
            elem = HTML(get_template(CURRENT_DIR, 'lgc/person_hr_list.html'))
        else:
            elem = (_('The profile for this person does not exist. Follow this link to create it: ') +
                    '&nbsp;<a href="' +
                    str(reverse_lazy('lgc-account-link', kwargs={'pk': obj.id})) +
                    '">' + _('create profile') + '</a><br><br>')
            elem = Div(HTML(elem), css_class='form-row')
        external_profile.append(elem)

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
                               HTML('<div class="form-group"><label for="id_process_name" class="col-form-label">&nbsp;</label><div class=""><button class="btn btn-outline-info" type="submit" onclick="return person_form_check();">' + _('Create') + '</button></div></div>'),
                               css_class='form-row'))

        process_tab.append(
            HTML(get_template(CURRENT_DIR, 'lgc/person_process_list.html')))
        tab_holder.append(process_tab)

        if obj.invoice_set.count():
            billing_tab = LgcTab(_('Billing'))
            billing_tab.append(HTML(get_template(CURRENT_DIR, 'lgc/file_invoice_list.html')))
            tab_holder.append(billing_tab)

    if external_profile != None:
        tab_holder.append(external_profile)

    if obj:
        documents_tab = LgcTab(_('Documents'))
        documents_tab.append(HTML(get_template(CURRENT_DIR,
                                               'lgc/document_form.html')))
        tab_holder.append(documents_tab)

    layout = Layout(tab_holder)
    layout.append(HTML('<button class="btn btn-outline-info" type="submit" onclick="return person_form_check();">' +
                       action + '</button>'))
    if obj and request.user.is_staff:
        layout.append(HTML('&nbsp;<a href="' +
                           str(reverse_lazy('lgc-file-delete', kwargs={'pk': obj.id})) +
                           '" class="btn btn-outline-info">' +
                           _('Delete') + '</a>'))
    form.helper.layout = layout
    return form

def employee_user_get_person_form_layout(request, form, action, obj):
    external_profile = None
    form.helper = FormHelper()
    form.helper.form_tag = False
    if obj == None or obj.user == None:
        return None

    info_tab = LgcTab(
        _('Information'),
        Div(Div('active_tab'),
            Div('first_name', css_class='form-group col-md-3'),
            Div('last_name', css_class='form-group col-md-3'),
            Div('email', css_class='form-group col-md-3'),
            Div('version'),
            css_class='form-row'),
        Div(
            Div('citizenship', css_class='form-group col-md-3'),
            Div('foreigner_id', css_class='form-group col-md-3'),
            Div('birth_date', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('passport_expiry', css_class='form-group col-md-3'),
            Div('passport_nationality', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('home_entity', css_class='form-group col-md-3'),
            Div('host_entity', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('home_entity_address', css_class='form-group col-md-3'),
            Div('host_entity_address', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('local_address', css_class='form-group col-md-3'),
            Div('local_phone_number', css_class='form-group col-md-3'),
            css_class='form-row'),
        Div(Div('foreign_address', css_class='form-group col-md-3'),
            Div('foreign_phone_number', css_class='form-group col-md-3'),
            Div('foreign_country', css_class='form-group col-md-3'),
            css_class='form-row'),
        get_spouse_information_div(request, form),
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
    layout.append(HTML('<button class="btn btn-outline-info" type="submit" onclick="return employee_form_check();">' +
                       action + '</button>'))
    form.helper.layout = layout
    return form

def get_person_form_layout(request, form, action, obj,
                           completed_processes=None):
    if request.user.role in user_models.get_internal_roles():
        return local_user_get_person_form_layout(request, form, action, obj,
                                                 completed_processes)
    if (request.user.role == user_models.ROLE_EMPLOYEE or
        request.user.role in user_models.get_hr_roles()):
        return employee_user_get_person_form_layout(request, form, action, obj)
    return None

class TemplateTimelineStages():
    is_done = False
    name = ''
    start_date = ''

def check_docs(obj, doc, docs):
    if not doc.is_valid():
        messages.error(obj.request, _('Invalid document.'))
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

        if stages:
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
        else:
            log.error('process %d of the file %d does not have stages',
                      person_process.id, self.object.id)

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
                expiration_queryset = models.Expiration.objects.filter(person=self.object, type__in=lgc_models.get_expiration_list())
                spouse_expiration_queryset = models.Expiration.objects.filter(person=self.object, type__in=lgc_models.get_spouse_expiration_list())
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
        if model == employee_models:
            if self.request.user.role in user_models.get_hr_roles():
                context['doc_download_url'] = 'hr-download-file'
            else:
                context['doc_download_url'] = 'employee-download-file'
        else:
            context['doc_download_url'] = 'lgc-download-file'

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
                                          self.get_formset_objs(model.Expiration.objects.filter(person=self.object, type__in=lgc_models.get_expiration_list())))]
        if self.is_spouse_expirations_diff:
            context['formsets_diff'] += [('spouse_expiration', _('Spouse Expirations'),
                                          self.get_formset_objs(model.Expiration.objects.filter(person=self.object, type__in=lgc_models.get_spouse_expiration_list())))]
        if self.is_archive_box_diff:
            context['formsets_diff'] += [('ab', _('Archive boxes'),
                                          self.get_formset_objs(lgc_models.ArchiveBox.objects.filter(person=self.object)))]
        if self.form_diff or len(context['formsets_diff']):
            changes_form = lgc_forms.ChangesDetectedForm()
            changes_form.helper = FormHelper()
            changes_form.helper.form_tag = False
            changes_form.helper.layout = Layout(
                Div(LgcRadio('changes_action'), css_class='form-row')
            )
            context['changes_detected_form'] = changes_form

        DocumentFormSet = modelformset_factory(lgc_models.Document,
                                               form=lgc_forms.DocumentFormSet,
                                               can_delete=True, extra=0)

        if self.object:
            if self.request.user.role in user_models.get_internal_roles():
                obj = self.object
                if (hasattr(self.object, 'user') and
                    hasattr(self.object.user, 'hr_employees')):
                    context['hr_list'] = self.object.user.hr_employees.all()
            else:
                emp_obj = self.get_object()
                obj = emp_obj.user.person_user_set

            doc_qs = lgc_models.Document.objects.filter(person=obj)
            if type(self.object).__name__ == 'Employee':
                doc_qs = doc_qs.filter(deleted=False)
            context['docs'] = DocumentFormSet(prefix='docs', queryset=doc_qs)
            context['process'] = lgc_models.PersonProcess.objects.filter(person=obj)
            if self.request.user.role in user_models.get_internal_roles():
                invoices = self.object.invoice_set.filter(type=lgc_models.INVOICE)
                pending_invoices = invoices.filter(state=lgc_models.INVOICE_STATE_PENDING)|invoices.filter(state=lgc_models.INVOICE_STATE_TOBEDONE).all()
                closed_invoices = invoices.exclude(state=lgc_models.INVOICE_STATE_PENDING).exclude(state=lgc_models.INVOICE_STATE_TOBEDONE).all()
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
                form.instance.employee_child_set.person = employee
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
                                                                  model.Expiration.objects.filter(person=self.object, type__in=lgc_models.get_expiration_list()))
            elif formset.id == 'spouse_expiration_id':
                self.is_spouse_expirations_diff = self.have_objs_changed(formset,
                                                                         model.Expiration.objects.filter(person=self.object, type__in=lgc_models.get_spouse_expiration_list()))
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
                if not form.errors.get('id'):
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
        if type(self.object) == employee_models.Employee:
            return
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

        if self.model.__name__ != 'Employee':
            for p in lgc_models.PROCESS_CHOICES_DEPRECATED:
                if form.instance.info_process == p[0]:
                    if 'info_process' not in form.changed_data:
                        break
                    messages.error(self.request, _('A deprecated immigration process cannot be used.'))
                    return super().form_invalid(form)

        if self.object:
            if (form.instance.is_private and self.object.user and
                self.object.user.hr_employees.count()):
                messages.error(self.request,
                               _('The private field cannot be set as HRs are linked with this file.'))
                return super().form_invalid(form)

            if (self.request.user.role in user_models.get_internal_roles() and
                self.object.state != lgc_models.FILE_STATE_CLOSED and
                form.cleaned_data['state'] == lgc_models.FILE_STATE_CLOSED and
                self.get_active_person_processes()):
                messages.error(self.request,
                               _('This file cannot be closed as it has a pending process.'))
                return super().form_invalid(form)

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
                       '"> ' + _('Click here to moderate it.') + '</a>')
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
            form_changed = False
            for cdata in form.changed_data:
                if cdata == 'updated' or cdata == 'user' or cdata == 'active_tab':
                    continue;
                form_changed = True
                break

            if form_changed or formsets[0].has_changed():
                form.instance.updated = True
            """self.object is valid as external users can only update the form."""
            person = self.object.user.person_user_set

        doc, deleted_docs = self.get_doc_forms()

        if type(self.object) == employee_models.Employee:
            docs = lgc_models.Document.objects.filter(person=person, deleted=False)
        else:
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
                session_cache_del(self.request.session, 'process_progress')

            for formset in formsets:
                self.delete_formset(formset)
                self.save_formset(formset)

            if form.instance.user:
                form.instance.user.first_name = form.instance.first_name
                form.instance.user.last_name = form.instance.last_name
                form.instance.user.email = form.instance.email

                if self.request.user.role in user_models.get_internal_roles():
                    form.instance.user.responsible.set(form.instance.responsible.all())
                    form.instance.user.save()

            if 'responsible' in form.changed_data:
                session_cache_del(self.request.session, 'process_progress')

            update_form = False
            if doc.cleaned_data['document'] != None:
                doc.instance = lgc_models.Document()
                doc.instance.document = doc.cleaned_data['document']
                doc.instance.description = doc.cleaned_data['description']
                doc.instance.person = person
                doc.instance.uploaded_by = self.request.user
                if type(self.object) == employee_models.Employee:
                    doc.instance.added = True
                    update_form = True
                doc.save()

            self.set_employee_data(form, formsets)

            if self.is_update and deleted_docs:
                for d in deleted_docs.deleted_forms:
                    if d.instance.id == None:
                        continue
                    if type(self.object) != employee_models.Employee:
                        try:
                            lgc_models.delete_person_doc(form.instance, d.instance)
                        except Exception as e:
                            messages.error(self.request,
                                           _('Cannot delete the file `%(filename)s`')%{
                                               'filename':d.instance.filename})
                            log.error(e)
                    else:
                        d.instance.deleted = True
                        d.instance.save()
                        update_form = True

            if update_form:
                form.instance.updated = True
                form.save()

            if (type(self.object) == employee_models.Employee and
                form.instance.updated):
                user_views.notify_user(self.object.user, self.object,
                                       lgc_types.MsgType.MODERATION)

        messages.success(self.request, self.success_message)
        return http.HttpResponseRedirect(self.get_success_url())

    def get_form(self, form_class=lgc_forms.PersonCreateForm):
        if self.request.user.role in user_models.get_internal_roles():
            form_class = lgc_forms.PersonCreateForm
        else:
            form_class = employee_forms.EmployeeUpdateForm
        form = super().get_form(form_class=form_class)

        if not self.is_update:
            return get_person_form_layout(self.request, form, _('Create'), None)
        return get_person_form_layout(self.request, form, _('Update'),
                                      self.object,
                                      lgc_models.PersonProcess.objects.filter(person=self.object.id, active=False))

    class Meta:
        abstract = True

class PersonCreateView(PersonCommonView, CreateView):
    title = ugettext_lazy('New File')
    is_update = False
    success_message = ugettext_lazy('File successfully created')

class PersonUpdateView(PersonCommonView, UpdateView):
    title = ugettext_lazy('File')
    is_update = True
    success_message = ugettext_lazy('File successfully updated')

def send_delete_email(request, user, success_msg):
    if (request.method == 'POST' and request.POST.get('inform_person') and
        request.POST['inform_person'] == 'on'):
        try:
            lgc_send_email(user, lgc_types.MsgType.DEL, request.user)
        except Exception as e:
            messages.error(request, _('Cannot send email to `%(email)s` (%(err)s)')%{
                'email':user.email, 'err': str(e)
            })
            raise

    messages.success(request, success_msg)

class PersonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = lgc_models.Person
    obj_name = ugettext_lazy('File')
    title = ugettext_lazy('Delete File')
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
        success_message = _("%(obj_name)s of %(firstname)s %(lastname)s deleted successfully.")%{
            'obj_name':self.obj_name,
            'firstname':self.object.first_name,
            'lastname':self.object.last_name,
        }

        if type(self.object).__name__ == 'User':
            if hasattr(self.object, 'person_user_set'):
                person_obj = self.object.person_user_set
            else:
                person_obj = None
        else:
            person_obj = self.object

        if person_obj and person_obj.document_set:
            for doc in person_obj.document_set.all():
                try:
                    lgc_models.delete_person_doc(self.object, doc)
                except Exception as e:
                    log.error(e)
                    messages.error(self.request, _('Cannot remove user files.'))
                    return redirect('lgc-account', self.object.id)

        if self.object.user:
            try:
                send_delete_email(self.request, self.object.user, success_message)
            except:
                return redirect('lgc-file', self.object.id)
        return super().delete(request, *args, **kwargs)

@login_required
def ajax_person_process_search_view(request, *args, **kwargs):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    pk = kwargs.get('pk', '')
    objects = lgc_models.PersonProcess.objects.filter(person=pk, active=False)
    term = request.GET.get('term', '')
    objs =  objects.filter(name_fr__istartswith=term)
    objs |= objects.filter(name_en__istartswith=term)
    objs = objs[:10]

    col_list = ['name_fr', 'name_en']
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
    objs =  model.objects.filter(name_fr__istartswith=term)
    objs |= model.objects.filter(name_en__istartswith=term)
    col_list = ['name_fr', 'name_en']
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
    template_name = 'lgc/process.html'
    model = lgc_models.Process

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
        billing_stages = []
        for s in lgc_models.ProcessStage.objects.all():
            if s.invoice_alert:
                billing_stages.append(s)
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
        return available_stages, billing_stages

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
    title = ugettext_lazy('Processes')
    create_url = reverse_lazy('lgc-process-create')
    item_url = 'lgc-process'
    this_url = reverse_lazy('lgc-processes')
    ajax_search_url = reverse_lazy('lgc-process-search-ajax')
    search_url = reverse_lazy('lgc-processes')

    def get_queryset(self):
        term = self.request.GET.get('term')
        order_by = self.get_ordering()
        if not term:
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
        if (self.model != lgc_models.PersonProcess and
            (self.request.user.is_staff or
             self.request.user.role == user_models.ROLE_CONSULTANT)):
            create_url = self.create_url
        else:
            create_url = None

        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['create_url'] = create_url
        context['item_url'] = self.item_url
        context['ajax_search_url'] = self.ajax_search_url
        context['search_url'] = self.search_url
        context['header_values'] = [
            ('id', 'ID'), ('name_fr', _('French Name')),
            ('name_en', _('English Name'))
        ]

        return pagination(self.request, context, self.this_url)

class ProcessCreateView(ProcessCommonView, SuccessMessageMixin, CreateView):
    success_message = ugettext_lazy('Process successfully created')
    success_url = reverse_lazy('lgc-process-create')
    title = ugettext_lazy('New Process')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        if self.model == lgc_models.Process:
            stages = self.get_available_stages(None)
            context['available_stages'] = stages[0]
            context['billing_stages'] = stages[1]
        return context

    def test_func(self):
        return (self.request.user.is_staff or
                self.request.user.role == user_models.ROLE_CONSULTANT)

    def get_form(self, form_class=lgc_forms.ProcessForm):
        return super().get_form(form_class=form_class)

class ProcessUpdateView(ProcessCommonView, SuccessMessageMixin, UpdateView):
    success_message = ugettext_lazy('Process successfully updated')
    success_url = 'lgc-process'
    title = ugettext_lazy('Process')
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
            stages = self.get_available_stages(self.object.stages)
            context['available_stages'] = stages[0]
            context['billing_stages'] = stages[1]
            context['stages'] = self.get_ordered_stages(self.object)
        if (not self.request.user.is_staff and
            self.request.user.role != user_models.ROLE_CONSULTANT):
            context['read_only'] = True
        return context

    def test_func(self):
        return (self.request.user.is_staff or
                self.request.user.role == user_models.ROLE_CONSULTANT)

class ProcessDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = lgc_models.Process
    template_name = 'lgc/process_confirm_delete.html'
    success_url = reverse_lazy('lgc-processes')
    title = ugettext_lazy('Delete Process')
    cancel_url = 'lgc-process'
    obj_name = ugettext_lazy('Process')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['cancel_url'] = reverse_lazy(self.cancel_url,
                                             kwargs={'pk':self.object.id})
        context['lang'] = translation.get_language()
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.process_set.count():
            if self.model == lgc_models.ProcessStage:
                url = 'lgc-process-stage'
                msg = _('This stage cannot be deleted as it is currently being used.')
            else:
                url = 'lgc-process'
                msg = _('This process cannot be deleted as it is currently being used.')
            messages.error(self.request, msg)
            return redirect(url, self.object.id)

        if translation.get_language() == 'fr':
            name = self.object.name_fr
        else:
            name = self.object.name_en
        success_message = (_("%(obj_name)s `%(name)s' successfully deleted."%
                           {'obj_name': self.obj_name, 'name': name }))
        messages.success(self.request, success_message)
        return super().delete(request, *args, **kwargs)

class ProcessStageListView(ProcessListView):
    model = lgc_models.ProcessStage
    title = ugettext_lazy('Process Stages')
    create_url = reverse_lazy('lgc-process-stage-create')
    item_url = 'lgc-process-stage'
    this_url = reverse_lazy('lgc-process-stages')
    ajax_search_url = reverse_lazy('lgc-process-stage-search-ajax')
    search_url = reverse_lazy('lgc-process-stages')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['header_values'] = [
            ('id', 'ID'), ('name_fr', _('French Name')),
            ('name_en', _('English Name')),
            ('invoice_alert', _('Generates invoice alert')),
        ]

        return context

class ProcessStageCreateView(ProcessCreateView):
    model = lgc_models.ProcessStage
    success_message = ugettext_lazy('Process stage successfully created')
    success_url = reverse_lazy('lgc-process-stage-create')
    title = ugettext_lazy('New Process Stage')
    template_name = 'lgc/generic_form.html'

    def get_form(self, form_class=lgc_forms.ProcessStageForm):
        return super().get_form(form_class=form_class)

class ProcessStageUpdateView(ProcessUpdateView):
    model = lgc_models.ProcessStage
    success_message = ugettext_lazy('Process stage successfully updated')
    success_url = 'lgc-process-stage'
    title = ugettext_lazy('Process Stage')
    delete_url = 'lgc-process-stage-delete'
    template_name = 'lgc/generic_form.html'

    def get_form(self, form_class=lgc_forms.ProcessStageForm):
        return super().get_form(form_class=form_class)

class ProcessStageDeleteView(ProcessDeleteView):
    model = lgc_models.ProcessStage
    success_url = reverse_lazy('lgc-process-stages')
    title = ugettext_lazy('Delete Process Stage')
    cancel_url = 'lgc-process-stage'
    obj_name = ugettext_lazy('Process stage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = translation.get_language()
        return context

class PersonProcessUpdateView(LoginRequiredMixin, UserPassesTestMixin,
                              SuccessMessageMixin, UpdateView):
    model = lgc_models.PersonProcess
    template_name = 'lgc/person_process.html'
    success_message = ugettext_lazy('Process successfully updated.')
    success_url = 'lgc-person-process'
    delete_url = ''
    fields = '__all__'

    def test_func(self):
        return self.request.user.role in user_models.get_internal_roles()

    def get_stage_forms(self):
        last_stage = self.get_last_person_process_stage(self.object.stages)

        if self.object.is_process_complete():
            stage_form = lgc_forms.UnboundFinalPersonProcessStageForm
        elif last_stage == None:
            if len(self.object.invoice_set.all()) == 0:
                stage_form = lgc_forms.UnboundPersonProcessInitialStageForm
            else:
                stage_form = lgc_forms.UnboundPersonProcessInitialStageForm2
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
        context['object'] = self.get_object()
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
                Div('version'),
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
                                           name_fr, name_en, process_stage):
        next_stage = lgc_models.PersonProcessStage()
        if not process_stage:
            next_stage.is_specific = True
        else:
            next_stage.process_stage = process_stage
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
        if person_process_stages == None or person_process_stages.count() == 0:
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

    def has_alert(self, person_process_stages, process):
        if person_process_stages == None:
            return False

        process_common = ProcessCommonView()
        process_stages = process_common.get_ordered_stages(process)
        if len(process_stages) == 0:
            return False

        pos = 0
        for s in person_process_stages.all():
            if s.is_specific:
                continue
            if process_stages[pos].invoice_alert:
                return True
            pos += 1
        return pos == len(process_stages)

    def form_valid(self, form):
        if self.object:
            self.object = self.get_object()
            if self.object.version != form.instance.version:
                msg = (_('This process has been modified by %(firstname)s %(lastname)s while you were editing it.')%{
                    'firstname':self.object.person.modified_by.first_name,
                    'lastname':self.object.person.modified_by.last_name,
                } +
                       '<a href="' +
                       str(reverse_lazy('lgc-person-process', kwargs={'pk':self.object.id})) +
                       '"> ' + _('Reload the page.'))
                messages.error(self.request, mark_safe(msg))
                return super().form_invalid(form)

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
            messages.error(self.request, _('Invalid stages form'))
            return super().form_invalid(form)

        for sform in formset:
            sform.save()

        action = stage_form.cleaned_data.get('action')
        if action == lgc_forms.PROCESS_STAGE_VALIDATE:
            next_process_stage = self.get_next_process_stage(self.object.stages,
                                                             self.object.process)
            if next_process_stage:
                self.generate_next_person_process_stage(self.object,
                                                        next_process_stage.name_fr,
                                                        next_process_stage.name_en,
                                                        next_process_stage)
            else:
                messages.error(self.request, _('The next stage does not exist.'))
                return super().form_invalid(form)
        elif action == lgc_forms.PROCESS_STAGE_DELETE:
            last_stage = self.get_last_person_process_stage(self.object.stages)
            if last_stage == None:
                messages.error(self.request, _('This process has no validated stages.'))
                return super().form_invalid(form)
            last_stage.delete()
            last_stage = self.get_last_person_process_stage(self.object.stages)
        elif action == lgc_forms.PROCESS_STAGE_DELETE_PROCESS:
            last_stage = self.get_last_person_process_stage(self.object.stages)
            if last_stage != None:
                messages.error(self.request, _('This process cannot be deleted as it has active stages.'))
                return super().form_invalid(form)
            if len(form.instance.invoice_set.all()) != 0:
                messages.error(self.request, _('This process cannot be deleted.'))
                return super().form_invalid(form)

            person_id = form.instance.person.id
            form.instance.delete()
            messages.success(self.request, _('Process successfully deleted.'))
            return redirect('lgc-file', person_id)

        elif action == lgc_forms.PROCESS_STAGE_ADD_SPECIFIC:
            if (specific_stage_form.cleaned_data['name_fr'] == '' or
                specific_stage_form.cleaned_data['name_en'] == ''):
                messages.error(self.request, _('The specific stage names are invalid.'))
                return super().form_invalid(form)

            self.generate_next_person_process_stage(self.object,
                                                    specific_stage_form.cleaned_data['name_fr'],
                                                    specific_stage_form.cleaned_data['name_en'],
                                                    None)

        elif action == lgc_forms.PROCESS_STAGE_COMPLETED:
            if not self.object.is_process_complete():
                messages.error(self.request, _('The process is not complete.'))
                return super().form_invalid(form)
            if (not form.instance.no_billing and
                len(form.instance.invoice_set.filter(type=lgc_models.INVOICE)) == 0):
                messages.error(self.request, _('This process cannot be closed as it does not have any invoice.'))
                return super().form_invalid(form)
            form.instance.active = False
            super().form_valid(form)
            return redirect('lgc-file', self.object.person.id)

        form.instance.version += 1
        form.instance.modification_date = timezone.now()
        session_cache_del(self.request.session, 'process_progress')
        if form.instance.no_billing:
            form.instance.invoice_alert = False
            return super().form_valid(form)

        if len(form.instance.invoice_set.filter(type=lgc_models.INVOICE)) == 0:
            form.instance.invoice_alert = self.has_alert(self.object.stages, self.object.process)
        if not self.object.invoice_alert:
            if self.object.is_process_complete():
                form.instance.invoice_alert = True
            if form.instance.invoice_alert:
                user_views.notify_user(self.object.person, self.object,
                                       lgc_types.MsgType.PROC_ALERT)
        return super().form_valid(form)

class PersonProcessListView(ProcessListView):
    model = lgc_models.PersonProcess
    create_url = None
    item_url = 'lgc-person-process'

    def get_ordering(self):
        return self.request.GET.get('order_by', 'id')

    def get_queryset(self, *args, **kwargs):
        pk = self.kwargs.get('pk', '')
        object_list = lgc_models.PersonProcess.objects.filter(person=pk, active=False)
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

        term = self.request.GET.get('term')
        order_by = self.get_ordering()
        if not term:
            return object_list.order_by(order_by)

        objs =  object_list.filter(name_fr__istartswith=term)
        objs |= object_list.filter(name_en__istartswith=term)
        objs.order_by(order_by)
        return objs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['header_values'] = [
            ('id', 'ID'), ('name_fr', _('French Name')),
            ('name_en', _('English Name')), ('get_name', _('Person Name')),
            ('get_file_id', _('File Id')),
        ]
        context['exclude_order_by'] = [ 'get_name', 'get_file_id' ]

        return context

class PersonProcessReadyListView(PersonProcessListView):
    title = ugettext_lazy('Processes ready to invoice')
    model = lgc_models.PersonProcess
    ajax_search_url = None
    search_url = reverse_lazy('lgc-person-processes-ready')
    item_url = 'lgc-person-process'
    objs = None
    pending_list = False

    def get_queryset(self, *args, **kwargs):
        if self.pending_list:
            if self.request.user.billing or self.request.user.is_staff:
                objs = lgc_models.PersonProcess.objects.filter(active=True)
            else:
                objs = lgc_models.PersonProcess.objects.filter(person__responsible=self.request.user,
                                                               active=True)
        else:
            if self.request.user.billing or self.request.user.is_staff:
                objs = lgc_models.PersonProcess.objects.filter(person__responsible=self.request.user,
                                                               invoice_alert=True)
            else:
                objs = lgc_models.PersonProcess.objects.filter(invoice_alert=True)

        objs2 = objs
        for p in objs2.all():
            if p.invoice_set.filter(type=lgc_models.INVOICE).count() > 0:
                objs = objs.exclude(id=p.id)

        term = self.request.GET.get('term')
        order_by = self.get_ordering()
        if not term:
            return objs.order_by(order_by)

        object_list =  objs.filter(name_fr__istartswith=term)
        object_list |= objs.filter(name_en__istartswith=term)
        object_list.order_by(order_by)
        return object_list

class PersonProcessPendingListView(PersonProcessReadyListView):
    title = ugettext_lazy('Pending Processes')
    model = lgc_models.PersonProcess
    search_url = reverse_lazy('lgc-person-processes-pending')
    pending_list = True

def get_account_layout(layout, new_token, is_hr=False, is_active=False,
                       initial=False):
    div = Div(css_class='form-row');
    if is_hr:
        layout.append(Div('active_tab'))

    layout.append(
        Div(
            Div('first_name', css_class='form-group col-md-3'),
            Div('last_name', css_class='form-group col-md-3'),
            Div('email', css_class='form-group col-md-3'),
            css_class='form-row'))
    if is_hr:
        hr_div = Div('company', css_class='form-group col-md-3')
    else:
        hr_div = None
    if initial:
        row_div = Div(
            Div('home_entity', css_class='form-group col-md-3'),
            Div('host_entity', css_class='form-group col-md-3'),
            css_class='form-row')
        layout.append(row_div)

    layout.append(
        Div(
            Div('responsible', css_class='form-group col-md-3'),
            Div('language', css_class='form-group col-md-3'),
            hr_div,
            css_class='form-row'))
    layout.append(div)

    if is_active:
        row_div = Div(css_class='form-row')
        row_div.append(Div('status', css_class='form-group col-md-3'))
        layout.append(row_div)

    row_div = Div(css_class='form-row')
    if new_token or is_hr:
        if new_token:
            row_div.append(Div('new_token', css_class='form-group col-md-3'))
        if is_hr:
            row_div.append(Div('is_admin', css_class='form-group col-md-3'))
        elif initial:
            row_div.append(Div('disabled', css_class='form-group col-md-3'))

    if is_active:
        row_div.append(Div('is_active', css_class='form-group col-md-3'))

    layout.append(row_div)

    return layout

def get_account_form(form, action, uid, is_staff=False, new_token=False):
    form.helper = FormHelper()
    if uid != None:
        initial=False
    else:
        initial=True
    form.helper.layout = get_account_layout(Layout(), new_token, is_hr=False,
                                            is_active=uid, initial=initial)

    form.helper.layout.append(
        HTML('<button class="btn btn-outline-info" type="submit">' +
             str(action) + '</button>'))
    if uid and is_staff:
        form.helper.layout.append(
            HTML(' <a href="{% url "lgc-account-delete" ' + str(uid) +
                 '%}" class="btn btn-outline-danger">' + str(delete_str) +
                 '</a>')
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

    if action:
        form.helper.layout.append(
            HTML('<button class="btn btn-outline-info" type="submit">' +
                 str(action) + '</button>'))
        if uid:
            form.helper.layout.append(
                HTML(' <a href="{% url "lgc-hr-delete" ' + str(uid) +
                     '%}" class="btn btn-outline-danger">' + str(delete_str) +
                     '</a>')
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
    form_class = lgc_forms.CreateAccountForm
    is_hr = False

    class Meta:
        abstract = True

    def test_func(self):
        return self.request.user.role in user_models.get_internal_roles()

class CreateAccount(AccountView, SuccessMessageMixin, CreateView):
    success_message = ugettext_lazy('New account successfully created')
    title = ugettext_lazy('Create access')
    form_name = ugettext_lazy('Create access')

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

    def get_form(self, form_class=lgc_forms.CreateAccountForm):
        form = super().get_form(form_class=self.form_class)

        if self.is_hr:
            return get_hr_account_form(form, self.form_name, None,
                                       new_token=True)
        form = get_account_form(form, self.form_name, None, new_token=True)
        if self.request.method == 'GET':
            hrid = self.request.GET.get('hr')

            try:
                hr = User.objects.get(id=hrid)
            except:
                hr = None

            form.fields['first_name'].initial = self.request.GET.get('fn')
            form.fields['last_name'].initial = self.request.GET.get('ln')
            form.fields['email'].initial = self.request.GET.get('e')
            form.fields['language'].initial = self.request.GET.get('l')
            if hr:
                form.fields['responsible'].initial = hr.responsible.all()

        return form

    def return_non_existant(self, form, pk):
        messages.error(self.request,
                       _("Cannot link with a non-existent file `%s'"%pk))
        return super().form_invalid(form)

    def get_person(self):
        pk = self.kwargs.get('pk')
        if not pk:
            return None
        try:
            p = lgc_models.Person.objects.get(id=pk)
        except:
            raise ValueError('invalid person ID')
        return p

    def check_person_exists(self, obj):
        objs = lgc_models.Person.objects.filter(first_name=obj.first_name,
                                                last_name=obj.last_name,
                                                home_entity=obj.home_entity,
                                                host_entity=obj.host_entity,
                                                is_private=False)
        if objs.count() > 0:
            messages.error(self.request,
                           _('A similar file (id: %(id)d) already exists.')%{
                               'id':objs[0].id
                           })
            return True

        if (obj.email and
            lgc_models.Person.objects.filter(email=obj.email).count() > 0):
            messages.error(self.request,
                           'A file with this email address already exists.')
            return True

        return False

    def form_valid(self, form):
        try:
            p = self.get_person()
        except:
            return self.return_non_existant(form, self.kwargs.get('pk', ''))

        self.object = form.save(commit=False)
        self.object.home_entity = form.cleaned_data['home_entity']
        self.object.host_entity = form.cleaned_data['host_entity']
        if self.check_person_exists(self.object):
            return super().form_invalid(form)

        form.instance.is_active = True

        if self.is_hr:
            if form.cleaned_data['is_admin']:
                form.instance.role = user_models.ROLE_HR_ADMIN
            else:
                form.instance.role = user_models.ROLE_HR
        else:
            form.instance.role = user_models.ROLE_EMPLOYEE
        if form.cleaned_data['new_token']:
            form.instance.token = token_generator()
            form.instance.token_date = timezone.now()
            if self.is_hr:
                type = lgc_types.MsgType.NEW_HR
            else:
                if form.cleaned_data['disabled']:
                    type = lgc_types.MsgType.NEW_EM_DISABLED
                    form.instance.is_active = False
                else:
                    type = lgc_types.MsgType.NEW_EM
            try:
                # add extra url parameters such as home|host entities
                lgc_send_email(self.object, type, self.request.user)
            except Exception as e:
                messages.error(self.request, _('Cannot send email to `%(email)s` (%(err)s)')%{
                    'email':self.object.email,
                    'err': str(e)
                })
                log.error(e)
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
    title = ugettext_lazy('Employee Accounts')
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
    success_message = ugettext_lazy('Account successfully updated')
    title = ugettext_lazy('Update Account')
    form_name = ugettext_lazy('Update')
    is_hr = False

    def get_success_url(self):
        return reverse_lazy(self.success_url, kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['formset_title'] = _('Employees')
        context['formset_add_text'] = _('Add an employee')
        if self.is_hr and self.object.role == user_models.ROLE_HR_ADMIN:
            context['form'].fields['is_admin'].initial = True
        context['form'].fields['new_token'].initial = False
        del context['user']
        if self.object and hasattr(self.object, 'person_user_set'):
            context['file_url'] = reverse_lazy('lgc-file', kwargs={'pk':self.object.person_user_set.id})
        return context

    def get_form(self, form_class=lgc_forms.UpdateAccountForm):
        form = super().get_form(form_class=self.form_class)

        if self.is_hr:
            """Do not show 'update' and 'delete' buttons for person not in charge"""
            if self.request.user in self.object.responsible.all():
                action = self.form_name
            else:
                action = None
            return get_hr_account_form(form, action, self.object.id,
                                       new_token=True)
        return get_account_form(form, self.form_name, self.object.id,
                                is_staff=self.request.user.is_staff,
                                new_token=True)

    def form_valid(self, form, relations = None):
        pending_user_err_msg = _('The status cannot be set to active as ' +
                                 'the user has not accepted our terms and ' +
                                 'condiftions yet.')

        try:
            user = User.objects.get(id=self.object.id)
        except:
            return self.form_invalid(form)

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
              self.object.role == user_models.ROLE_EMPLOYEE):
            messages.error(self.request, pending_user_err_msg)
            return redirect('lgc-account', self.object.id)

        if self.is_hr:
            if form.cleaned_data['is_admin']:
                form.instance.role = user_models.ROLE_HR_ADMIN
            else:
                form.instance.role = user_models.ROLE_HR
        else:
            form.instance.role = user_models.ROLE_EMPLOYEE

        if form.cleaned_data['new_token']:
            form.instance.token = token_generator()
            form.instance.token_date = timezone.now()
            form.instance.password = ''

            if self.is_hr:
                type = lgc_types.MsgType.NEW_HR
            else:
                if not form.cleaned_data['is_active']:
                    type = lgc_types.MsgType.NEW_EM_DISABLED
                    form.instance.is_active = False
                else:
                    type = lgc_types.MsgType.NEW_EM
            try:
                lgc_send_email(self.object, type, self.request.user)
            except Exception as e:
                messages.error(self.request, _('Cannot send email to `%(email)s` (%(err)s)')%{
                    'email':self.object.email,
                    'err': str(e)
                })
                log.error(e)
                return super().form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('There are errors on the page'))
        return super().form_invalid(form)

class DeleteAccount(AccountView, DeleteView):
    obj_name = ugettext_lazy('Account')
    title = ugettext_lazy('Delete Account')
    success_url = reverse_lazy('lgc-accounts')
    template_name = 'lgc/person_confirm_delete.html'

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
        success_message = _("Account of `%(firstname)s %(lastname)s' deleted successfully.")%{
            'firstname':self.object.first_name,
            'lastname':self.object.last_name,
        }

        if (hasattr(self.object, 'person_user_set') and
            hasattr(self.object.person_user_set, 'document_set')):
            for doc in self.object.person_user_set.document_set.all():
                try:
                    lgc_models.delete_person_doc(self.object.person_user_set, doc)
                except Exception as e:
                    log.error(e)
                    messages.error(self.request, _('Cannot remove user files.'))
                    return redirect('lgc-account', self.object.id)
        try:
            send_delete_email(self.request, self.object, success_message)
        except:
            return redirect('lgc-account', self.object.id)

        if hasattr(self.object, 'person_user_set'):
            self.object.person_user_set.delete()
        return super().delete(request, args, kwargs)

class HRView(LoginRequiredMixin):
    req_type = lgc_types.ReqType.HR
    model = User
    success_url = 'lgc-hr'
    delete_url = 'lgc-hr-delete'
    create_url = reverse_lazy('lgc-hr-create')
    update_url = 'lgc-hr'
    cancel_url = 'lgc-hr'
    list_url = reverse_lazy('lgc-hr-accounts')
    form_class = lgc_forms.CreateHRForm
    is_hr = True

    class Meta:
        abstract = True

    def test_func(self):
        return self.request.user.role in user_models.get_internal_roles()

class HRCreateView(HRView, CreateAccount):
    success_message = ugettext_lazy('New HR account successfully created')
    title = ugettext_lazy('New HR account')
    form_name = ugettext_lazy('Create account')

    def test_func(self):
        return (self.request.user.role == user_models.ROLE_CONSULTANT or
                self.request.user.is_staff)

class HRUpdateView(HRView, UpdateAccount, UserPassesTestMixin):
    success_message = ugettext_lazy('HR account successfully updated')
    title = ugettext_lazy('Update HR')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset_title'] = ''
        context['formset_add_text'] = _('Add an employee')
        EmployeeFormSet = formset_factory(lgc_forms.HREmployeeForm,
                                          extra=0, can_delete=True)

        if self.request.user in self.object.responsible.all():
            context['is_editable'] = True
        else:
            context['is_editable'] = False

        set_active_tab(self, context)
        if self.request.POST:
            context['formset'] = EmployeeFormSet(self.request.POST)
        else:
            init = []
            for p in self.object.hr_employees.all():
                if p.role != user_models.ROLE_EMPLOYEE:
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
            if e.cleaned_data.get('id') and e.cleaned_data['id'] == id:
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
            u = users.get(id=e['id'])
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
    title = ugettext_lazy('HR accounts')
    template_name = 'lgc/accounts.html'
    ajax_search_url = reverse_lazy('user-hr-search-ajax')
    search_url = reverse_lazy('lgc-hr-accounts')
    users = user_models.get_hr_user_queryset()

class HRDeleteView(HRView, DeleteAccount):
    success_url = reverse_lazy('lgc-hr-accounts')
    obj_name = ugettext_lazy('HR account')
    title = ugettext_lazy('Delete HR account')
    template_name = 'lgc/person_confirm_delete.html'

@login_required
def settings_view(request):
    if not request.user.billing:
        raise Http404

    if request.method == 'POST':
        form = lgc_forms.SettingsForm(request.POST)
        if form.is_valid():
            settings = form.save(commit=False)
            settings.rate_EUR = 1
            settings.id = 1
            settings.save()
            messages.success(request, _('Settings successfully updated'))
        else:
            messages.error(request, _('Cannot save'))
    else:
        slen = lgc_models.Settings.objects.count()
        if slen == 0:
            settings = lgc_models.Settings()
            settings.rate_EUR = 1
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
            Div('rate_EUR', css_class='form-group col-md-1 bg-info'),
            Div('rate_USD', css_class='form-group col-md-1'),
            Div('rate_CAD', css_class='form-group col-md-1'),
            Div('rate_GBP', css_class='form-group col-md-1'),
            css_class='form-row'),
        HTML('<button class="btn btn-outline-info" type="submit">' +
        _('Update') + '</button>'))
    form.fields['rate_EUR'].widget.attrs['readonly'] = True

    context = {
        'title': _('Settings'),
        'form': form,
    }
    return render(request, 'lgc/generic_form_with_formsets.html', context)

@login_required
def ajax_insert_employee_view(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    term = request.GET.get('term', '')
    users = user_models.get_employee_user_queryset().filter(person_user_set__is_private=False)
    employees = users.filter(first_name__istartswith=term)|users.filter(last_name__istartswith=term)|users.filter(email__istartswith=term)
    employees = employees[:10]

    set_bold_search_attrs(employees, ['first_name', 'last_name', 'email'], term)
    context = {
        'employees': employees
    }
    return render(request, 'lgc/insert_employee.html', context)

def ajax_file_search_find_exact_objs(objs, term, res):
    objects = objs.filter(first_name=term)[:1]
    if len(objects):
        res.append(objects[0])
    objects = objs.filter(last_name=term)[:1]
    if len(objects):
        res.append(objects[0])
    objects = objs.filter(last_name=term)[:1]
    if len(objects):
        res.append(objects[0])

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

    term = request.GET.get('term')

    """ ignore empty requests """
    if not term:
        return

    objs = lgc_models.Person.objects
    all_objs = []

    ajax_file_search_find_exact_objs(objs, term, all_objs)
    eterm = term + ' '
    files = ajax_file_search_find_objs(objs, eterm)[:10-len(all_objs)]
    for obj in files:
        all_objs.append(obj)
    cnt = len(all_objs)

    if cnt < 10:
        files = (objs.filter(first_name__istartswith=term).exclude(first_name=term)|
                 objs.filter(last_name__istartswith=term).exclude(last_name=term)|
                 objs.filter(email__istartswith=term).exclude(email=term))[:10-cnt]

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
    try:
        doc = lgc_models.Document.objects.get(id=pk)
    except:
        raise Http404

    if not user_access_test(request, doc.person.user):
        return http.HttpResponseForbidden()

    file_path = os.path.join(settings.MEDIA_ROOT, doc.document.name)
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
    expires = request.GET.get('expires')
    expiry_type = request.GET.get('expiry_type')
    show_disabled = request.GET.get('show_disabled')
    show_expired = request.GET.get('show_expired')
    user = request.GET.get('user')
    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')

    """ initial value of 'expires' must be set """
    if not expires:
        request.GET = request.GET.copy()
        request.GET['expires'] = settings.EXPIRATIONS_NB_DAYS
        if request.user.role not in user_models.get_hr_roles():
            request.GET['user'] = request.user.id
        if (request.user.role in user_models.get_internal_roles() and
            request.user.role != user_models.ROLE_NONE):
            objs = objs.filter(person__responsible=request.user)
    try:
        delta = datetime.timedelta(days=int(expires))
    except:
        delta = datetime.timedelta(days=settings.EXPIRATIONS_NB_DAYS)
    compare_date = timezone.now().date() + delta
    objs = objs.filter(end_date__lte=compare_date)

    if user:
        try:
            user = User.objects.get(id=user)
        except:
            raise Http404
        objs = objs.filter(person__responsible=user)

    if expiry_type:
        objs = objs.filter(type=expiry_type)
    if not show_disabled:
        objs = objs.filter(enabled=True)
    if not show_expired:
        objs = objs.exclude(end_date__lte=timezone.now().date())
    if first_name:
        objs = objs.filter(person__first_name=first_name)
    if last_name:
        objs = objs.filter(person__last_name=last_name)
    return objs

def get_expirations_form(request, show_expiry_type=True):
    if len(request.GET):
        form = lgc_forms.ExpirationSearchForm(request.GET)
    else:
        form = lgc_forms.ExpirationSearchForm()
        form.fields['expires'].initial = settings.EXPIRATIONS_NB_DAYS
        form.fields['user'].initial = request.user
    form.helper = FormHelper()
    form.helper.form_method = 'get'
    form.helper.layout = Layout(
        Div(
            Div('user', css_class='form-group col-md-3'),
            Div('expires', css_class='form-group col-md-3'),
            Div('expiry_type', css_class='form-group col-md-3') if show_expiry_type else None,
            Div('show_disabled', css_class='form-group col-md-2 lgc_aligned_checkbox'),
            Div('show_expired', css_class='form-group col-md-3 lgc_aligned_checkbox'),
            css_class='form-row'),
    )
    return form

@login_required
def __expirations(request, form, objs):
    context = {
        'title': 'Expirations',
        'search_form': form,
    }
    context = pagination(request, context, reverse_lazy('lgc-expirations'),
                         'end_date')

    if objs:
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
            log.info('expirations: obj.id:%d type:%s child-set-len:%d employee-child-set-len:%d',
                     obj.id, obj.type, len(obj.child_set.all()),
                     len(obj.employee_child_set.all()))
            log.info('fixed detached child %d expiration', obj.id)
            obj.delete()

    return __expirations(request, form, objs)

def get_revenue(start_date, end_date, currency):
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d')
    invoices = lgc_models.Invoice.objects.filter(state=lgc_models.INVOICE_STATE_PAID,
                                                 currency=currency,
                                                 last_modified_date__range=[start_date, end_date])
    month_total = 0.

    for invoice in invoices:
        month_total += float(invoice.total)

    return round(month_total, 2)

def get_this_year_revenue():
    end_date = datetime.date.today()
    start_date = end_date.replace(day=1)
    currencies = { 'EUR', 'USD', 'CAD', 'GBP' }
    year_revenue = []

    for i in range(start_date.month, 0, -1):
        month_name = start_date.strftime("%b")
        month = start_date.month
        rev = {}
        year_revenue.append((month_name, month, rev))

        for currency in currencies:
            rev[currency] = get_revenue(start_date, end_date, currency)

        end_date = start_date - datetime.timedelta(days=1)
        start_date = end_date.replace(day=1)

    return year_revenue

@login_required
def stats_view(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    nb_files = lgc_models.Person.objects.count()
    nb_active_files = lgc_models.Person.objects.filter(state=lgc_models.FILE_STATE_ACTIVE).count()
    nb_internal_users = user_models.get_all_local_user_queryset().count()
    nb_external_users = user_models.get_external_user_queryset().count()

    user_stats = []
    users = user_models.get_local_user_queryset().filter(is_superuser=False, is_active=True).order_by('first_name')
    compare_date = (timezone.now().date() +
                    datetime.timedelta(days=settings.EXPIRATIONS_NB_DAYS))
    nb_active_files_per_user = {}
    for u in users:
        active_files = u.person_resp_set.filter(state=lgc_models.FILE_STATE_ACTIVE).count()
        nb_active_files_per_user[u.email] = active_files
        if active_files:
            active_files_percent = round((active_files / nb_active_files) * 100)
        else:
            active_files_percent = 0
        expirations = lgc_models.Expiration.objects.filter(enabled=True, person__responsible=u, end_date__lte=compare_date).exclude(end_date__lte=timezone.now().date())
        wp = (expirations.filter(type=lgc_models.EXPIRATION_TYPE_WP)|
              expirations.filter(type=lgc_models.EXPIRATION_TYPE_SWP)).count()
        rp = expirations.exclude(type=lgc_models.EXPIRATION_TYPE_WP).exclude(type=lgc_models.EXPIRATION_TYPE_SWP).count()

        user_stats.append((u, u.person_resp_set.count(), active_files,
                           active_files_percent, wp, rp))

    context = session_cache_get(request.session, 'stats')
    if context:
        context['user_stats'] = user_stats
        ret = render(request, 'lgc/statistics.html', context)
        del context['user_stats']
        return ret

    crossed_list = []
    consultants = users.filter(role__exact=user_models.ROLE_CONSULTANT,
                               is_active=True)
    active_files_no_jurists = []
    for j in users.filter(role__exact=user_models.ROLE_JURIST, is_active=True):
        persons = j.person_resp_set.get_queryset().filter(state=lgc_models.FILE_STATE_ACTIVE)
        cons_juri_list = []

        for c in consultants:
            person = persons.filter(responsible__id=c.id)
            cons = {
                'first_name': c.first_name,
                'last_name': c.last_name,
            }
            juri = {
                'first_name': j.first_name,
                'last_name': j.last_name,
            }
            element = {
                'cons': cons,
                'juri': juri,
                'count': person.count(),
            }
            cons_juri_list.append(element)

            if hasattr(c, 'cnt'):
                continue
            prsns = c.person_resp_set.get_queryset().filter(state=lgc_models.FILE_STATE_ACTIVE).exclude(responsible__role=user_models.ROLE_JURIST)
            c.cnt = prsns.count()
            if nb_active_files_per_user[c.email]:
                cnt = (c.cnt / nb_active_files_per_user[c.email]) * 100
            else:
                cnt = 0
            active_files_no_jurists.append(round(cnt))
        crossed_list.append(cons_juri_list)

    nb_max = max(nb_files, nb_active_files, nb_internal_users,
                 nb_external_users)
    if nb_max < 100:
        max_level = 10
    elif nb_max < 1000:
        max_level = 30
    elif nb_max < 10000:
        max_level = 60
    else:
        max_level = 90

    if nb_max == nb_files:
        nb_files_level = max_level
        nb_active_files_level = (max_level / nb_files) * nb_active_files
        nb_internal_users_level = (max_level / nb_files) * nb_internal_users
        nb_external_users_level = (max_level / nb_files) * nb_external_users
    elif nb_max == nb_internal_users:
        nb_internal_users_level = max_level
        nb_files_level = (max_level / nb_internal_users) * nb_files
        nb_active_files_level = (max_level / nb_internal_users) * nb_active_files
        nb_external_users_level = (max_level / nb_internal_users) * nb_external_users
    elif nb_max == nb_external_users:
        nb_external_users_level = max_level
        nb_files_level = (max_level / nb_external_users) * nb_files
        nb_active_files_level = (max_level / nb_external_users) * nb_active_files
        nb_internal_users_level = (max_level / nb_external_users) * nb_internal_users
    else:
        log.error('incoherent statistics')
        nb_files_level = 0
        nb_active_files_level = 0
        nb_internal_users_level = 0
        nb_external_users_level = 0

    if request.user.billing:
        this_year_revenue = get_this_year_revenue()
    else:
        this_year_revenue = None
    context = {
        'title': _('Statistics'),
        'nb_files': nb_files,
        'nb_active_files': nb_active_files,
        'nb_internal_users': nb_internal_users,
        'nb_external_users': nb_external_users,
        'nb_files_level': nb_files_level,
        'nb_active_files_level': nb_active_files_level,
        'nb_internal_users_level': nb_internal_users_level,
        'nb_external_users_level': nb_external_users_level,

        'nb_hr': user_models.get_hr_user_queryset().count(),
        'crossed_list': crossed_list,
        'active_files_no_jurists': active_files_no_jurists,
        'expirations': lgc_models.Expiration.objects.filter(enabled=True).exclude(end_date__lte=timezone.now().date()).count(),
        'year_revenue': this_year_revenue,
        'nb_processes': lgc_models.Process.objects.count(),
    }

    session_cache_add(request.session, 'stats', context, 30)

    """Session handling is asynchronious."""
    context = context.copy()
    context['user_stats'] = user_stats

    return render(request, 'lgc/statistics.html', context)
