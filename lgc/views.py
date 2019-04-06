from django.db import transaction
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from common.utils import pagination, lgc_send_email, must_be_staff
from common.lgc_types import ReqType, ReqAction
from django import http
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils import translation
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin

from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  DeleteView)
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from . import models as lgc_models
from . import forms as lgc_forms
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
from users import models as user_models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from common import lgc_types
import string
import random
import datetime
import os

contact_admin = _('Please contact your administrator.')

User = get_user_model()
CURRENT_DIR = Path(__file__).parent
delete_str = _('Delete')

def token_generator():
    size = 64
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits

    while True:
        r = ''.join(random.choice(chars) for _ in range(size))
        if len(User.objects.filter(token=r)) == 0:
            return r

def set_active_tab(obj, context):
    if obj.request.POST:
            obj.request.session['active_tab'] = obj.request.POST.get('active_tab')
            return
    active_tab = obj.request.session.get('active_tab')
    if active_tab:
        del obj.request.session['active_tab']
        context['form'].fields['active_tab'].initial = active_tab

@login_required
def home(request):
    return render(request, 'lgc/index.html', {'title':'Home'})

@login_required
def tables(request):
    return render(request, 'lgc/tables.html', {'title':'Tables'})

class PersonCommonListView(LoginRequiredMixin, ListView):
    template_name = 'lgc/files.html'
    model = lgc_models.Person
    ajax_search_url = reverse_lazy('lgc-file-search-ajax')
    search_url = reverse_lazy('lgc-files')

    class Meta:
        abstract = True

    def get_ordering(self):
        return self.request.GET.get('order_by', '-id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Files')
        context['create_url'] = reverse_lazy('lgc-file-create')
        context['update_url'] = 'lgc-file'
        context['ajax_search_url'] = self.ajax_search_url
        context['search_url'] = self.search_url

        return pagination(self, context, reverse_lazy('lgc-files'))

    def test_func(self):
        if self.request.user.role not in user_models.get_internal_roles():
            return False
        return True

class PersonListView(PersonCommonListView):
    def get_queryset(self):
        term = self.request.GET.get('term', '')
        order_by = self.get_ordering()
        if term == '':
            return lgc_models.Person.objects.order_by(order_by)
        objs = (lgc_models.Person.objects.filter(email__istartswith=term)|
                lgc_models.Person.objects.filter(first_name__istartswith=term)|
                lgc_models.Person.objects.filter(last_name__istartswith=term))
        return objs.order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_id'] = True
        context['show_birth_date'] = True
        return context

def get_template(name):
    try:
        with Path(CURRENT_DIR, 'templates', 'lgc', name).open() as fh:
            return fh.read()
    except FileNotFoundError:
        raise Http404

def local_user_get_person_form_layout(form, action, obj, process_stages,
                                      archived_processes):
    external_profile = None
    form.helper = FormHelper()
    form.helper.form_tag = False

    info_tab = LgcTab(
        _('Information'),
        Div(Div('active_tab'),
            Div('first_name', css_class='form-group col-md-4'),
            Div('last_name', css_class='form-group col-md-4'),
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
        Div(Div('prefecture', css_class='form-group col-md-4'),
            Div('subprefecture', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('consulate', css_class='form-group col-md-4'),
            Div('direccte', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('jurisdiction', css_class='form-group col-md-4'),
            css_class='form-row'),
    )

    info_tab.append(Div(Div(HTML(get_template('formsets_template.html')),
                            css_class='form-group col-md-10'),
                        css_class='form-row'))
    info_tab.append(Div(Div('state', css_class='form-group col-md-4'),
                        Div('start_date', css_class='form-group col-md-4'),
                        css_class='form-row'))
    info_tab.append(Div(Div('comments', css_class='form-group col-md-8'),
            css_class='form-row'))

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

    process_tab = LgcTab(_('Process'))
    if archived_processes:
        process_tab.append(HTML('<a href="' +
                                str(reverse_lazy('lgc-person-processes',
                                                 kwargs={'pk': obj.id})) +
                                '">Archived processes (' +
                                str(len(archived_processes)) +
                                ')</a><br><br>'))
    if process_stages:
        pcontent = HTML(get_template('process_stages_template.html'))
    else:
        pcontent = Div(Div('process_name', css_class='form-group col-md-4'),
                       css_class='form-row')
    process_tab.append(pcontent)
    billing_tab = LgcTab(_('Billing'))

    documents_tab = LgcTab(_('Documents'))
    documents_tab.append(HTML(get_template('document_form.html')))

    tab_holder = TabHolder(info_tab)

    if external_profile != None:
        tab_holder.append(external_profile)

    tab_holder.append(process_tab)
    tab_holder.append(billing_tab)
    tab_holder.append(documents_tab)

    layout = Layout(tab_holder)
    layout.append(HTML('<button class="btn btn-outline-info" type="submit">' +
                       action + '</button>'))
    form.helper.layout = layout
    return form

def employee_user_get_person_form_layout(form, action, obj, process):
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
    )

    info_tab.append(Div(Div(HTML(get_template('formsets_template.html')),
                            css_class='form-group col-md-10'),
                        css_class='form-row'))

    tab_holder = TabHolder(info_tab)
    if process:
        process_tab = LgcTab(_('Process'))
        process_tab.append(HTML(get_template('process_stages_template.html')))
        tab_holder.append(process_tab)

    documents_tab = LgcTab(_('Documents'))
    documents_tab.append(HTML(get_template('document_form.html')))
    tab_holder.append(documents_tab)

    layout = Layout(tab_holder)
    layout.append(HTML('<button class="btn btn-outline-info" type="submit">' +
                       action + '</button>'))
    form.helper.layout = layout
    return form

def get_person_form_layout(cur_user, form, action, obj, process_stages,
                           archived_processes=None):
    if cur_user.role in user_models.get_internal_roles():
        return local_user_get_person_form_layout(form, action, obj,
                                                 process_stages,
                                                 archived_processes)
    if cur_user.role == user_models.EMPLOYEE:
        return employee_user_get_person_form_layout(form, action, obj,
                                                    process_stages)
    if cur_user.role in user_model.get_hr_roles():
        return
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

class PersonCommonView(LoginRequiredMixin, SuccessMessageMixin):
    model = lgc_models.Person
    is_update = False
    template_name = 'lgc/generic_form_with_formsets.html'

    def get_success_url(self):
        return reverse_lazy('lgc-file', kwargs={'pk': self.object.id})

    def get_active_person_process(self):
        if self.object == None:
            return
        process = lgc_models.PersonProcess.objects.filter(person=self.object.id).filter(active=True)
        if process.count() > 1:
            messages.error(self.request,
                           _('PersonProcess consistency error! ') +
                           contact_admin)
            return None
        if process.count() == 1:
            return process[0]
        return None

    def get_person_process_stages(self, person_process):
        if person_process == None:
            return None
        stages = lgc_models.PersonProcessStage.objects.filter(person_process=person_process)
        if stages.count() == 0:
            messages.error(self.request,
                           _('PersonProcessStage consistency error! ') +
                           contact_admin)
            return None
        return stages

    def get_process_stages(self, process):
        if process == None:
            return None
        processes = lgc_models.Process.objects.filter(id=process.id)
        if processes == None or processes.count() != 1:
            return None
        if processes[0].stages == None or processes[0].stages.count() == 0:
            return None
        return processes[0].stages

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
        next_stage.save()

    def get_next_process_stage(self, person_process_stages, process_id):
        process_common = ProcessCommonView()
        process_stages = process_common.get_ordered_stages(process_id)

        if person_process_stages == None:
            if process_stages == None or len(process_stages) == 0:
                return None
            return process_stages[0]
        person_process_stages = person_process_stages.filter(is_specific=False)
        if (person_process_stages == None or
            person_process_stages.count() == 0):
            return process_stages.first()

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

    def get_timeline_stages(self, person_process, person_process_stages):
        process_common = ProcessCommonView()
        timeline_stages = []
        for s in person_process_stages:
            timeline_stage = TemplateTimelineStages()
            timeline_stage.is_done = True
            if translation.get_language() == 'fr':
                timeline_stage.name = s.name_fr
            else:
                timeline_stage.name = s.name_en
            timeline_stage.start_date = s.start_date
            timeline_stages.append(timeline_stage)

        to_skip = person_process_stages.filter(is_specific=False).count()
        stages = process_common.get_ordered_stages(person_process.process.id)
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

    def is_process_complete(self, process_stages, person_process_stages):
        person_process_stages = person_process_stages.filter(is_specific=False)
        return len(process_stages.all()) == len(person_process_stages.all())

    def set_person_formsets_data(self, formsets):
        formsets[0].title = _('Children')
        formsets[0].id = 'children_id'
        formsets[0].err_msg = _('Invalid Children table')

        formsets[1].title = _('Visas or Residence Permits')
        formsets[1].id = 'visas_id'
        formsets[1].err_msg = _('Invalid Visas table')

        formsets[2].title = _("Spouse's Visas or Residence Permits")
        formsets[2].id = 'spouse_visas_id'
        formsets[2].err_msg = _("Invalid Spouse's Visas table")

        formsets[3].title = _('Work Permits')
        formsets[3].id = 'wp_id'
        formsets[3].err_msg = _('Invalid Work Permits table')

        formsets[4].title = _("Spouse's Work Permits")
        formsets[4].id = 'spouse_wp_id'
        formsets[4].err_msg = _("Invalid Spouse's Work Permits table")

        if self.request.user.role in user_models.get_internal_roles():
            formsets[5].title = _('Archive boxes')
            formsets[5].id = 'ab_id'
            formsets[5].err_msg = _('Invalid archive box number')

    def get_person_formsets(self):
        formsets = []
        ChildrenFormSet = modelformset_factory(lgc_models.Child,
                                               form=lgc_forms.ChildCreateForm,
                                               can_delete=True)

        VisaFormSet = modelformset_factory(lgc_models.VisaResidencePermit,
                                           form=lgc_forms.VisaResidencePermitForm,
                                           can_delete=True)
        SpouseVisaFormSet = modelformset_factory(lgc_models.SpouseVisaResidencePermit,
                                                 form=lgc_forms.SpouseVisaResidencePermitForm,
                                                 can_delete=True)
        WorkPermitFormSet = modelformset_factory(lgc_models.WorkPermit,
                                                 form=lgc_forms.WorkPermitForm,
                                                 can_delete=True)
        SpouseWorkPermitFormSet = modelformset_factory(lgc_models.SpouseWorkPermit,
                                                       form=lgc_forms.SpouseWorkPermitForm,
                                                       can_delete=True)
        if self.request.user.role in user_models.get_internal_roles():
            ArchiveBoxFormSet = modelformset_factory(lgc_models.ArchiveBox,
                                                     form=lgc_forms.ArchiveBoxForm,
                                                     can_delete=True)

        if self.request.POST:
            formsets.append(ChildrenFormSet(self.request.POST, prefix='children'))
            formsets.append(VisaFormSet(self.request.POST, prefix='visa'))
            formsets.append(SpouseVisaFormSet(self.request.POST, prefix='spouse_visa'))
            formsets.append(WorkPermitFormSet(self.request.POST, prefix='wp'))
            formsets.append(SpouseWorkPermitFormSet(self.request.POST, prefix='spouse_wp'))
            if self.request.user.role in user_models.get_internal_roles():
                formsets.append(ArchiveBoxFormSet(self.request.POST, prefix='ab'))
            self.set_person_formsets_data(formsets)
            return formsets

        if self.is_update:
            children_queryset = lgc_models.Child.objects.filter(person=self.object.id)
            visas_queryset = lgc_models.VisaResidencePermit.objects.filter(person=self.object.id)
            spouse_visas_queryset = lgc_models.SpouseVisaResidencePermit.objects.filter(person=self.object.id)
            wp_queryset = lgc_models.WorkPermit.objects.filter(person=self.object.id)
            wp_spouse_queryset = lgc_models.SpouseWorkPermit.objects.filter(person=self.object.id)
            archive_box_queryset = lgc_models.ArchiveBox.objects.filter(person=self.object.id)
        else:
            children_queryset = lgc_models.Child.objects.none()
            visas_queryset = lgc_models.VisaResidencePermit.objects.none()
            spouse_visas_queryset = lgc_models.VisaResidencePermit.objects.none()
            wp_queryset = lgc_models.WorkPermit.objects.none()
            wp_spouse_queryset = lgc_models.WorkPermit.objects.none()
            if self.request.user.role in user_models.get_internal_roles():
                archive_box_queryset = lgc_models.ArchiveBox.objects.none()
        formsets.append(ChildrenFormSet(queryset=children_queryset,
                                        prefix='children'))
        formsets.append(VisaFormSet(queryset=visas_queryset,
                                    prefix='visa'))
        formsets.append(SpouseVisaFormSet(queryset=spouse_visas_queryset,
                                          prefix='spouse_visa'))
        formsets.append(WorkPermitFormSet(queryset=wp_queryset,
                                          prefix='wp'))
        formsets.append(SpouseWorkPermitFormSet(queryset=wp_spouse_queryset,
                                                prefix='spouse_wp'))
        if self.request.user.role in user_models.get_internal_roles():
            formsets.append(ArchiveBoxFormSet(queryset=archive_box_queryset,
                                              prefix='ab'))

        self.set_person_formsets_data(formsets)
        return formsets

    def set_person_process_stages(self, context):
        person_process = self.get_active_person_process()
        if person_process == None:
            return

        stages = self.get_process_stages(person_process.process)
        if stages == None or stages.count() == 0:
            return

        stagesFormSet = modelformset_factory(lgc_models.PersonProcessStage,
                                             form=lgc_forms.PersonProcessStageForm,
                                             can_delete=False,
                                             extra=0)

        # render all the stages, only the last one should be editable
        person_process_stages = self.get_person_process_stages(person_process)
        context['stages'] = stagesFormSet(queryset=person_process_stages)
        context['specific_stage'] = lgc_forms.PersonProcessSpecificStageForm()
        if self.request.user.role in user_models.get_internal_roles():
            context['person_process'] = person_process
        context['consulate_prefecture'] = lgc_forms.ConsulatePrefectureForm(instance=person_process)
        if self.is_process_complete(person_process.process.stages,
                                    person_process_stages):
            context['stage'] = lgc_forms.UnboundFinalPersonProcessStageForm()
        else:
            context['stage'] = lgc_forms.UnboundPersonProcessStageForm()
        context['stage'].fields['stage_comments'].initial = self.get_last_person_process_stage(person_process_stages).stage_comments
        context['timeline_stages'] = self.get_timeline_stages(person_process, person_process_stages)
        context['process_name'] = person_process.process.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        DocumentFormSet = modelformset_factory(lgc_models.Document,
                                               form=lgc_forms.DocumentFormSet,
                                               can_delete=True, extra=0)

        if self.object:
            context['docs'] = DocumentFormSet(prefix='docs', queryset=lgc_models.Document.objects.filter(person=self.object))
            context['process'] = lgc_models.PersonProcess.objects.filter(person=self.object)
        context['formsets'] = self.get_person_formsets()
        self.set_person_process_stages(context)

        set_active_tab(self, context)
        if self.request.POST:
            context['stage'] = lgc_forms.PersonProcessStageForm(self.request.POST)
            context['doc'] = lgc_forms.DocumentForm(self.request.POST,
                                                     self.request.FILES)
            context['deleted_docs'] = DocumentFormSet(self.request.POST, self.request.FILES,
                                                      prefix='docs')
        else:
            context['doc'] = lgc_forms.DocumentForm()
            if not self.is_update:
                context['form'].fields['start_date'].initial = str(datetime.date.today())

        return context

    def save_formset_instances(self, instances):
        for i in instances:
            i.person_id = self.object.id
            i.save()

    def process_form_valid(self, form):
        if self.request.user.role not in user_models.get_internal_roles():
            return 0

        person_process = self.get_active_person_process()
        if form.cleaned_data['process_name'] and person_process == None:
            person_process = lgc_models.PersonProcess()
            person_process.person = self.object
            person_process.process = form.cleaned_data['process_name']
            person_process.consulate = form.cleaned_data['consulate']
            person_process.prefecture = form.cleaned_data['prefecture']
            process_stages = self.get_process_stages(person_process.process)

            if process_stages == None:
                messages.error(self.request, 'The process has no stages.')
                return -1

            first_stage = self.get_next_process_stage(None, person_process.process.id)
            if first_stage == None:
                messages.error(self.request,
                               _('Cannot find the first stage of the process.'))
                return -1

            person_process.save()
            self.generate_next_person_process_stage(person_process,
                                                    first_stage.name_fr,
                                                    first_stage.name_en)
            return 0

        elif person_process == None:
            return 0

        # Process handling
        process_stages = self.get_process_stages(person_process.process)
        if process_stages == None:
            messages.error(self.request, 'The process has no stages.')
            return -1

        person_process_stages = self.get_person_process_stages(person_process)
        if person_process_stages == None:
            messages.error(self.request, 'The person process has no stages.')
            return -1

        person_process_stage = self.get_last_person_process_stage(person_process_stages)
        if person_process_stage == None:
            messages.error(self.request, 'Cannot get the person process last stage.')
            return -1

        if self.is_process_complete(person_process.process.stages,
                                    person_process_stages):
            stage_form = lgc_forms.UnboundFinalPersonProcessStageForm(self.request.POST)
        else:
            stage_form = lgc_forms.UnboundPersonProcessStageForm(self.request.POST)
        if not stage_form.is_valid():
            return -1
        if stage_form.cleaned_data['action'] == lgc_forms.PROCESS_STAGE_DELETE:
            if person_process_stages.count() == 1:
                person_process_stage.delete()
                person_process.delete()
                return 0

            person_process_stage.delete()
            messages.success(self.request, _('Last stage deleted'))
            return 0

        person_process_stage.stage_comments = stage_form.cleaned_data['stage_comments']

        if stage_form.cleaned_data['action'] == lgc_forms.PROCESS_STAGE_VALIDATE:
            next_process_stage = self.get_next_process_stage(person_process_stages,
                                                             person_process.process.id)
            if next_process_stage != None:
                self.generate_next_person_process_stage(person_process,
                                                        next_process_stage.name_fr,
                                                        next_process_stage.name_en)
        elif stage_form.cleaned_data['action'] == lgc_forms.PROCESS_STAGE_ADD_SPECIFIC:
            specific_stage = lgc_forms.PersonProcessSpecificStageForm(self.request.POST)
            if (not specific_stage.is_valid() or
                specific_stage.cleaned_data['name_fr'] == '' or
                specific_stage.cleaned_data['name_en'] == ''):
                messages.error(self.request, _('Invalid specific stage name'))
                return -1
            self.generate_next_person_process_stage(person_process,
                                                    specific_stage.cleaned_data['name_fr'],
                                                    specific_stage.cleaned_data['name_en'],
                                                    is_specific=True)
        elif stage_form.cleaned_data['action'] == lgc_forms.PROCESS_STAGE_ARCHIVE:
            person_process.active = False
        elif stage_form.cleaned_data['action'] == lgc_forms.PROCESS_STAGE_GEN_INVOICE_AND_ARCHIVE:
            person_process.active = False

        person_process.save()
        person_process_stage.save()
        return 0

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        if form.instance.start_date == None:
            form.instance.start_date = str(datetime.date.today())
        context = self.get_context_data()

        with transaction.atomic():
            for formset in context['formsets']:
                if not formset.is_valid():
                    messages.error(self.request, formset.err_msg)
                    return super().form_invalid(form)

                for obj in formset.deleted_forms:
                    if (obj.instance.id != None):
                        obj.instance.delete()

            if self.is_update and self.object.user != None:
                form.instance.user = self.object.user

            self.object = form.save()
            for formset in context['formsets']:
                instances = formset.save(commit=False)
                self.save_formset_instances(instances)
            doc = context['doc']
            if not doc.is_valid():
                messages.error(self.request, _('Invalid document.'))
                return super().form_invalid(form)

            if doc.cleaned_data['document'] != None:
                if doc.cleaned_data['description'] == '':
                    messages.error(self.request, _('Invalid document description.'))
                    return super().form_invalid(form)
                doc.instance = lgc_models.Document()
                doc.instance.document = doc.cleaned_data['document']

                if doc.instance.document.size > settings.MAX_FILE_SIZE << 20:
                    messages.error(self.request, _('File too big. Maximum file size is %dM.')%
                                   settings.MAX_FILE_SIZE)
                    return super().form_invalid(form)

                docs = lgc_models.Document.objects.filter(person=self.object)
                for d in docs.all():
                    if d.document.name != doc.instance.document.name:
                        continue
                    messages.error(self.request, _("File `%s' already exists.")%
                                   d.document.name)
                    return super().form_invalid(form)

                doc.instance.description = doc.cleaned_data['description']
                doc.instance.person = form.instance
                doc.instance.uploaded_by = self.request.user
                doc.save()

            for d in context['deleted_docs'].deleted_forms:
                if d.instance.id != None:
                    d.instance.delete()
                    os.remove(os.path.join(settings.MEDIA_ROOT,
                                           d.instance.document.name))

        if self.process_form_valid(form) < 0:
            return super().form_invalid(form)

        return super().form_valid(form)

    def get_form(self, form_class=lgc_forms.PersonCreateForm):
        if self.request.user.role in user_models.get_internal_roles():
            form_class = lgc_forms.PersonCreateForm
        else:
            form_class = lgc_forms.EmployeeUpdateForm
        form = super().get_form(form_class=form_class)
        if not self.is_update:
            return get_person_form_layout(self.request.user, form,
                                          _('Create'), None, None)
        return get_person_form_layout(self.request.user, form, _('Update'),
                                      self.object,
                                      self.get_active_person_process(),
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

def myfile(request):
    view = PersonUpdateView.as_view()
    return view(request, pk=request.user.person_user_set.id)

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
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_message = _("%s of %s %s deleted successfully.")%(
            self.obj_name, self.object.first_name, self.object.last_name
        )
        messages.success(self.request, success_message)
        if (self.request.method == 'POST' and
            self.request.POST.get('inform_person') and
            self.request.POST['inform_person'] == 'on'):
            try:
                lgc_send_email(self.object, lgc_types.MsgType.DEL)
            except Exception as e:
                messages.error(self.request, _('Cannot send email to') + '`'
                               + self.object.email + '`: ' + str(e))
                return super().form_invalid(form)
        return super().delete(request, *args, **kwargs)

@login_required
def ajax_process_search_view(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    term = request.GET.get('term', '')
    objs = lgc_models.Process.objects.filter(name__istartswith=term)
    objs = objs[:10]

    for o in objs:
        if term in o.name.lower():
            o.b_name = o.name.lower()
    context = {
        'objects': objs
    }
    return render(request, 'lgc/process_search.html', context)

@login_required
def ajax_person_process_search_view(request, *args, **kwargs):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    pk = kwargs.get('pk', '')
    objects = lgc_models.PersonProcess.objects.filter(person=pk).filter(active=False)
    term = request.GET.get('term', '')
    objs = objects.filter(process__name__istartswith=term)
    objs = objs[:10]

    for o in objs:
        if term in o.process.name.lower():
            o.b_name = o.process.name.lower()
    context = {
        'objects': objs
    }
    return render(request, 'lgc/process_search.html', context)

@login_required
def ajax_process_stage_search_view(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    term = request.GET.get('term', '')
    objs = (lgc_models.ProcessStage.objects.filter(name_fr__istartswith=term)|
            lgc_models.ProcessStage.objects.filter(name_en__istartswith=term))
    objs = objs[:10]

    for o in objs:
        if term in o.name_fr.lower():
            o.b_name = o.name_fr.lower()
        elif term in o.name_en.lower():
            o.b_name = o.name_en.lower()
    context = {
        'objects': objs
    }
    return render(request, 'lgc/process_search.html', context)

class ProcessCommonView(LoginRequiredMixin):
    def test_func(self):
        if self.request.user.role not in user_models.get_internal_roles():
            return False
        return True

    def get_ordered_stages(self, process_id):
        process_stages = lgc_models.Process.objects.filter(id=process_id).all()
        if process_stages == None or len(process_stages) == 0:
            return None
        process_stages = process_stages[0].stages
        all_process_stages = lgc_models.ProcessStage.objects
        objects = []

        for s in process_stages.through.objects.filter(process_id=process_id).order_by('id').all():
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

    class Meta:
        abstract = True

class ProcessListView(ProcessCommonView, ListView):
    template_name = 'lgc/processes.html'
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
        objs = self.model.objects.filter(name__istartswith=term)
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
        return pagination(self, context, self.this_url)

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
            context['stages'] = self.get_ordered_stages(self.object.id)
        return context

    def form_valid(self, form):
        if self.model != lgc_models.Process:
            return super().form_valid(form)

        """ always save the stages. This will keep their order. """
        with transaction.atomic():
            form.instance.stages.clear()
            for s in form.data.getlist('stages'):
                form.instance.stages.add(s)
            form.instance.save()
        return super().form_valid(form)

    def get_form(self, form_class=lgc_forms.ProcessForm):
        return super().get_form(form_class=form_class)

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
        success_message = _("%s %s successfully deleted.")%(self.obj_name,
                                                            self.object.id)
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = translation.get_language()
        for obj in context['object_list']:
            if lang == 'fr':
                obj.name = obj.name_fr
            else:
                obj.name = obj.name_en
        return context

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

class PersonProcessUpdateView(ProcessUpdateView):
    model = lgc_models.PersonProcess
    template_name = 'lgc/person_process.html'
    title = _('Person Process')
    delete_url = ''
    fields = '__all__'

    def get_context_data(self, **kwargs):
        person_common = PersonCommonView()
        context = super().get_context_data(**kwargs)
        context['consulate_prefecture'] = lgc_forms.ConsulatePrefectureForm(instance=self.object)
        context['person_process'] = self.object
        person_process_stages = person_common.get_person_process_stages(self.object)
        context['timeline_stages'] = person_common.get_timeline_stages(self.object, person_process_stages)
        stagesFormSet = modelformset_factory(lgc_models.PersonProcessStage,
                                             form=lgc_forms.PersonProcessStageForm,
                                             can_delete=False,
                                             extra=0)

        context['stages'] = stagesFormSet(queryset=person_process_stages)
        context['go_back'] = self.request.META.get('HTTP_REFERER')
        return context

    def get_form(self):
        form = super().get_form()
        form.helper = FormHelper()
        form.helper.layout = Layout(HTML(get_template('process_stages_template.html')))
        return form

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
        for obj in context['object_list']:
            obj.name = obj.process.name
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
        self.title = (_('Archived Processes of ') +
                      "%s %s"%(person.first_name, person.last_name))

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

    if new_token or is_hr:
        row_div = Div(css_class='form-row')
        if new_token:
            row_div.append(Div('new_token', css_class='form-group col-md-4'))
        if is_hr:
            row_div.append(Div('is_admin', css_class='form-group col-md-4'))
        layout.append(row_div)

    return layout

def get_account_form(form, action, uid, new_token=False):
    form.helper = FormHelper()
    form.helper.layout = get_account_layout(Layout(), new_token, False, uid)

    form.helper.layout.append(
        HTML('<button class="btn btn-outline-info" type="submit">' +
             action + '</button>'))
    if uid:
        form.helper.layout.append(
            HTML(' <a href="{% url "lgc-account-delete" ' + str(uid) +
                 '%}" class="btn btn-outline-danger">' + delete_str + '</a>')
        )
    return form

def get_hr_account_form(form, action, uid, new_token=False, show_tabs=True):
    form.helper = FormHelper()
    if show_tabs:
        form.helper.layout = Layout(TabHolder(
            LgcTab(_('Information'), get_account_layout(Layout(), new_token,
                                                     True, uid)),
            LgcTab(_('Employees'),
                Div(Div(HTML(get_template('employee_list.html')),
                        css_class="form-group col-md-10"),
                    css_class="form-row")),
        ))
    else:
        form.helper.layout = get_account_layout(Layout(), new_token,
                                                is_hr=True)

    form.helper.layout.append(
        HTML('<button class="btn btn-outline-info" type="submit">' +
             action + '</button>'))
    if uid:
        form.helper.layout.append(
            HTML(' <a href="{% url "lgc-hr-delete" ' + str(uid) +
                 '%}" class="btn btn-outline-danger">' + delete_str + '</a>')
        )

    return form

class AccountView(LoginRequiredMixin):
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
    title = _('Initiate a case')
    form_name = _('Initiate case')

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
            return get_hr_account_form(form, self.form_name, None, True,
                                       False)
        return get_account_form(form, self.form_name, None, True)

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
            p.save()
        return ret

    def form_invalid(self, form):
        messages.error(self.request, _('There are errors on the page'))
        return super().form_invalid(form)

class Accounts(AccountView, PersonCommonListView, UserPassesTestMixin):
    title = _('Employee Accounts')
    template_name = 'lgc/accounts.html'
    ajax_search_url = reverse_lazy('lgc-employee-user-search-ajax')
    search_url = reverse_lazy('lgc-accounts')
    users = user_models.get_employee_user_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['create_url'] = self.create_url
        context['update_url'] = self.update_url

        return pagination(self, context, self.list_url)

    def get_queryset(self):
        term = self.request.GET.get('term', '')
        options = self.request.GET.get('options', '')
        if options == 'pending':
            users = self.users.filter(GDPR_accepted=None)
        elif options == 'refused':
            users = self.users.filter(GDPR_accepted=False)
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
        return context

    def get_form(self, form_class=lgc_forms.InitiateAccountForm):
        form = super().get_form(form_class=self.form_class)

        if self.is_hr:
            return get_hr_account_form(form, self.form_name, self.object.id,
                                       True, True)
        return get_account_form(form, self.form_name, self.object.id, True)

    def form_valid(self, form, relations = None):
        self.object = form.save(commit=False)

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

class HRView(LoginRequiredMixin):
    req_type = ReqType.HR
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
        if self.request.user.role not in user_models.get_hr_roles() + user_models.get_internal_roles():
            return False
        return True

class HRCreateView(HRView, InitiateAccount):
    success_message = _('New HR account successfully initiated')
    title = _('New HR account')
    form_name = _('Initiate account')

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
    ajax_search_url = reverse_lazy('lgc-hr-user-search-ajax')
    search_url = reverse_lazy('lgc-hr-accounts')
    users = user_models.get_hr_user_queryset()

class HRDeleteView(HRView, DeleteAccount):
    success_url = reverse_lazy('lgc-hr-accounts')
    obj_name = _('HR account')
    title = _('Delete HR account')
    template_name = 'lgc/person_confirm_delete.html'

@login_required
@must_be_staff
def ajax_insert_employee_view(request):
    term = request.GET.get('term', '')
    users = user_models.get_employee_user_queryset()
    employees = users.filter(first_name__istartswith=term)|users.filter(last_name__istartswith=term)|users.filter(email__istartswith=term)
    employees = employees[:10]

    for f in employees:
        if term in f.first_name.lower():
            f.b_first_name = f.first_name.lower()
        elif term in f.last_name.lower():
            f.b_last_name = f.last_name.lower()
        elif term in f.email.lower():
            f.b_email = f.email.lower()

    context = {
        'employees': employees
    }
    return render(request, 'lgc/insert_employee.html', context)

@login_required
def ajax_file_search_view(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    term = request.GET.get('term', '')
    files = lgc_models.Person.objects.filter(first_name__istartswith=term)|lgc_models.Person.objects.filter(last_name__istartswith=term)|lgc_models.Person.objects.filter(email__istartswith=term)
    files = files[:10]

    for f in files:
        if term in f.first_name.lower():
            f.b_first_name = f.first_name.lower()
        elif term in f.last_name.lower():
            f.b_last_name = f.last_name.lower()
        elif term in f.email.lower():
            f.b_email = f.email.lower()

    context = {
        'users': files
    }
    return render(request, 'users/search.html', context)

@login_required
def download_file(request, *args, **kwargs):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    pk = kwargs.get('pk', '')
    doc = lgc_models.Document.objects.filter(id=pk).all()
    if doc == None or len(doc) != 1:
        raise Http404

    file_path = os.path.join(settings.MEDIA_ROOT, doc[0].document.name)
    if not os.path.exists(file_path):
        raise Http404
    with open(file_path, 'rb') as fh:
        res = http.HttpResponse(fh.read(), content_type='application/octet-stream')
        res['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
        return res
    raise Http404
