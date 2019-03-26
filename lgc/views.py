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
from common import lgc_types
import string
import random
import datetime

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

@login_required
def home(request):
    return render(request, 'lgc/index.html', {'title':'Home'})

@login_required
def tables(request):
    return render(request, 'lgc/tables.html', {'title':'Tables'})

class PersonCommonListView(LoginRequiredMixin, ListView):
    template_name = 'lgc/files.html'
    model = lgc_models.Person
    fields = '__all__'
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

def local_user_get_person_form_layout(form, action, obj, process_stages):
    external_profile = None
    form.helper = FormHelper()
    info_tab = Tab(
        _('Information'),
        Div(Div('first_name', css_class='form-group col-md-4'),
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
            Div('sous_prefecture', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('consulat', css_class='form-group col-md-4'),
            Div('direccte', css_class='form-group col-md-4'),
            css_class='form-row'),
        Div(Div('juridiction', css_class='form-group col-md-4'),
            css_class='form-row'),
    )

    #if obj and obj.user:
    #    info_tab.append(Div(Div('HR', css_class='form-group col-md-4'),
    #                        css_class='form-row'))
    info_tab.append(Div(Div(HTML(get_template('formsets_template.html')),
                            css_class='form-group col-md-10'),
                        css_class='form-row'))
    info_tab.append(Div(Div('state', css_class='form-group col-md-4'),
                        Div('start_date', css_class='form-group col-md-4'),
                        css_class='form-row'))
    info_tab.append(Div(Div('comments', css_class='form-group col-md-8'),
            css_class='form-row'))

    if obj:
        external_profile = Tab(_('Account Profile'))
        if obj.user:
            pdiv = Div(
                HTML(_("Click here to manage this person's account profile: ") +
                     '&nbsp;<a href="' +
                     str(reverse_lazy('lgc-account',
                                      kwargs={'pk': obj.user.id})) +
                     '">' + _('update profile') + '</a><br><br>'),
                css_class='form-row')
        else:
            pdiv = Div(
                HTML(_('The profile for this person does not exist. Follow this link to create it: ') +
                     '&nbsp;<a href="' +
                     str(reverse_lazy('lgc-account-link',
                                      kwargs={'pk': obj.id})) +
                     '">' + _('create profile') + '</a><br><br>'),
                css_class='form-row')
        external_profile.append(pdiv)

    process_tab = Tab(_('Process'))
    if process_stages:
        process_tab.append(HTML(get_template('process_stages_template.html')))
        #pdiv = Div(Div(HTML('{% load crispy_forms_tags %}{{ stages|crispy }}'),
        #               css_class='form-group col-md-4'),
        #           css_class='form-row')
        pdiv = None
    else:
        pdiv = Div(
            Div('process_name', css_class='form-group col-md-4'),
            css_class='form-row')
    process_tab.append(pdiv)

    billing_tab = Tab(_('Billing'),
    )
    tab_holder = TabHolder(info_tab)

    if external_profile:
        tab_holder.append(external_profile)

    tab_holder.append(process_tab)
    tab_holder.append(billing_tab)
    layout = Layout(tab_holder)
    layout.append(HTML('<button class="btn btn-outline-info" type="submit">' +
                       action + '</button>'))
    form.helper.layout = layout
    return form

def employee_user_get_person_form_layout(form, action, obj, process):
    external_profile = None
    form.helper = FormHelper()
    if obj == None or obj.user == None:
        print("Error")
        return

    info_tab = Tab(
        _('Information'),
        Div(Div('first_name', css_class='form-group col-md-4'),
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

    process_tab = Tab(_('Process'),
        #Div(Div(HTML('{% load crispy_forms_tags %}{{ process|crispy }}')),
        #        css_class='form-group col-md-4'),
        #    css_class='form-row'),
        Div(Div('process_name', css_class='form-group col-md-4'),
            css_class='form-row'),
    )

    tab_holder = TabHolder(info_tab)
    tab_holder.append(process_tab)

    layout = Layout(tab_holder)
    layout.append(HTML('<button class="btn btn-outline-info" type="submit">' +
                       action + '</button>'))
    form.helper.layout = layout
    return form

def get_person_form_layout(cur_user, form, action, obj, process_stages):
    if cur_user.role in user_models.get_internal_roles():
        return local_user_get_person_form_layout(form, action, obj,
                                                 process_stages)
    if cur_user.role == user_models.EMPLOYEE:
        return employee_user_get_person_form_layout(form, action, obj,
                                                    process_stages)
    if cur_user.role in user_model.get_hr_roles():
        #return hr_user_get_person_form_layout(form, action, obj,
        # process_stages)
        return

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

class PersonCommonView(LoginRequiredMixin, SuccessMessageMixin):
    model = lgc_models.Person
    fields = '__all__'
    is_update = False
    template_name = 'lgc/generic_form_with_formsets.html'

    def get_success_url(self):
        return reverse_lazy('lgc-file', kwargs={'pk': self.object.id})

    def get_active_person_process(self):
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

    def generate_next_person_process_stage(self, person_process, stage):
        next_stage = lgc_models.PersonProcessStage()
        next_stage.person_process = person_process
        next_stage.start_date = str(datetime.date.today())
        next_stage.name_fr = stage.name_fr
        next_stage.name_en = stage.name_en
        next_stage.save()

    def get_next_process_stage(self, process_stages, process_stage):
        if process_stage == None:
            return process_stages.first()

        length = len(process_stages.all())
        pos = 0
        for s in process_stages.all():
            if s.id != process_stage.id:
                pos += 1
                continue
            if pos == length:
                return process_stages.all()[pos]
            try:
                return process_stages.all()[pos + 1]
            except:
                return None
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.is_update:
            context['title'] = _('New File')
        else:
            context['title'] = _('File')
        context['process'] = lgc_models.PersonProcess.objects.filter(person=self.object)
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
        formsets = []
        if self.request.POST:
            formsets.append(ChildrenFormSet(self.request.POST,
                                            prefix='children'))
            formsets.append(VisaFormSet(self.request.POST,
                                        prefix='visa'))
            formsets.append(SpouseVisaFormSet(self.request.POST,
                                              prefix='spouse_visa'))
            formsets.append(WorkPermitFormSet(self.request.POST,
                                              prefix='wp'))
            formsets.append(SpouseWorkPermitFormSet(self.request.POST, prefix='spouse_wp'))
            context['stage'] = lgc_forms.PersonProcessStageForm(self.request.POST)
        else:
            if not self.is_update:
                context['form'].fields['start_date'].initial = str(datetime.date.today())
                children_queryset = lgc_models.Child.objects.none()
                visas_queryset = lgc_models.VisaResidencePermit.objects.none()
                spouse_visas_queryset = lgc_models.VisaResidencePermit.objects.none()
                wp_queryset = lgc_models.WorkPermit.objects.none()
                wp_spouse_queryset = lgc_models.WorkPermit.objects.none()
            else:
                person_process = self.get_active_person_process()
                if person_process:
                    stages = self.get_process_stages(person_process.process)
                else:
                    stages = None
                if person_process and stages and stages.count():
                    stagesFormSet = modelformset_factory(lgc_models.PersonProcessStage,
                                                         form=lgc_forms.PersonProcessStageForm,
                                                         can_delete=False,
                                                         extra=0)

                    # render all the stages, only the last one should be editable
                    person_process_stages = self.get_person_process_stages(person_process)
                    context['stages'] = stagesFormSet(queryset=person_process_stages)
                    context['stage'] = lgc_forms.UnboundPersonProcessStageForm()
                    context['stage'].fields['stage_comments'].initial = self.get_last_person_process_stage(person_process_stages).stage_comments
                    stages_tbd = []

                    i = len(context['stages'])
                    for s in person_process.process.stages.all():
                        if i:
                            i -= 1
                            continue
                        if translation.get_language() == 'fr':
                            stages_tbd.append(s.name_fr)
                        else:
                            stages_tbd.append(s.name_en)

                    context['stages_tbd'] = stages_tbd
                    context['process_name'] = person_process.process.name

                children_queryset = lgc_models.Child.objects.filter(person=self.object.id)
                visas_queryset = lgc_models.VisaResidencePermit.objects.filter(person=self.object.id)
                spouse_visas_queryset = lgc_models.SpouseVisaResidencePermit.objects.filter(person=self.object.id)
                wp_queryset = lgc_models.WorkPermit.objects.filter(person=self.object.id)
                wp_spouse_queryset = lgc_models.SpouseWorkPermit.objects.filter(person=self.object.id)

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

        context['formsets'] = formsets
        return context

    def save_formset_instances(self, instances):
        for i in instances:
            i.person_id = self.object.id
            i.save()

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
                #hr_add_employee(form.cleaned_data, self.object.user)
                form.instance.user = self.object.user

            self.object = form.save()
            for formset in context['formsets']:
                instances = formset.save(commit=False)
                self.save_formset_instances(instances)

        person_process = self.get_active_person_process()
        if form.cleaned_data['process_name'] and person_process == None:
            person_process = lgc_models.PersonProcess()
            person_process.person = self.object
            person_process.process = form.cleaned_data['process_name']
            process_stages = self.get_process_stages(person_process.process)

            if process_stages == None:
                messages.error(self.request, 'The process has no stages.')
                return super().form_valid(form)

            first_stage = self.get_next_process_stage(process_stages, None)
            if first_stage == None:
                messages.error(self.request,
                               _('Cannot find the first stage of the process.'))
                return super().form_valid(form)

            person_process.current_stage = first_stage
            person_process.save()
            self.generate_next_person_process_stage(person_process, first_stage)
        elif person_process != None:
            process_stages = self.get_process_stages(person_process.process)
            if process_stages == None:
                messages.error(self.request, 'The process has no stages.')
                return super().form_valid(form)

            person_process_stages = self.get_person_process_stages(person_process)
            if person_process_stages == None:
                messages.error(self.request, 'The person process has no stages.')
                return super().form_valid(form)

            person_process_stage = self.get_last_person_process_stage(person_process_stages)
            if person_process_stage == None:
                messages.error(self.request, 'Cannot get the person process last stage.')
                return super().form_valid(form)


            stage_form = lgc_forms.UnboundPersonProcessStageForm(self.request.POST)
            if not stage_form.is_valid():
                return super().form_invalid(form)
            person_process_stage.stage_comments = stage_form.cleaned_data['stage_comments']
            if stage_form.cleaned_data['validate_stage']:
                next_process_stage = self.get_next_process_stage(process_stages,
                                                                 person_process.current_stage)
                if next_process_stage != None:
                    self.generate_next_person_process_stage(person_process,
                                                            next_process_stage)
                    person_process.current_stage = next_process_stage
                    person_process.save()
            person_process_stage.save()

        return super().form_valid(form)

    def get_form(self, form_class=lgc_forms.PersonCreateForm):
        form = super().get_form(form_class=form_class)
        if not self.is_update:
            return get_person_form_layout(self.request.user, form,
                                          _('Create'), None, None)
        return get_person_form_layout(self.request.user, form, _('Update'),
                                      self.object,
                                      self.get_active_person_process())

    def form_invalid(self, form):
        context = self.get_context_data()

        for formset in context['formsets']:
            if not formset.is_valid():
                messages.error(self.request, formset.err_msg)
        return super().form_invalid(form)

    class Meta:
        abstract = True

class PersonCreateView(PersonCommonView, CreateView):
    is_update = False
    success_message = _('File successfully created')

class PersonUpdateView(PersonCommonView, UpdateView):
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

class ProcessListView(LoginRequiredMixin, ListView):
    template_name = 'lgc/processes.html'
    model = lgc_models.Process
    fields = '__all__'
    title = _('Processes')
    create_url = reverse_lazy('lgc-process-create')
    item_url = 'lgc-process'
    this_url = reverse_lazy('lgc-processes')

    def get_ordering(self):
        return self.request.GET.get('order_by', 'id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['create_url'] = self.create_url
        context['item_url'] = self.item_url

        return pagination(self, context, self.this_url)

class ProcessCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = lgc_models.Process
    fields = '__all__'
    success_message = _('Process successfully created')
    template_name = 'lgc/generic_form.html'
    success_url = reverse_lazy('lgc-process-create')
    title = _('New Process')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title

        return context

    def test_func(self):
        return self.request.user.is_staff

    def get_form(self, form_class=lgc_forms.ProcessForm):
        return super().get_form(form_class=form_class)

class ProcessUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = lgc_models.Process
    fields = ['name']
    success_message = _('Process successfully updated')
    success_url = 'lgc-process'
    template_name = 'lgc/generic_form.html'
    title = _('Process')
    delete_url = 'lgc-process-delete'

    def get_success_url(self):
        self.object = self.get_object()
        return reverse_lazy(self.success_url, kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['delete_url'] = reverse_lazy(self.delete_url,
                                             kwargs={'pk':self.object.id})
        return context

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
        success_message = _("%s %s deleted successfully.")%(self.obj_name,
                                                            self.object.id)
        messages.success(self.request, success_message)
        return super().delete(request, *args, **kwargs)

class ProcessStageListView(ProcessListView):
    model = lgc_models.ProcessStage
    title = _('Process Stages')
    create_url = reverse_lazy('lgc-process-stage-create')
    item_url = 'lgc-process-stage'
    this_url = reverse_lazy('lgc-process-stages')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = translation.get_language()
        return context

class ProcessStageCreateView(ProcessCreateView):
    model = lgc_models.ProcessStage
    success_message = _('Process stage successfully created')
    success_url = reverse_lazy('lgc-process-stage-create')
    title = _('New Process Stage')

    def get_form(self, form_class=lgc_forms.ProcessStageForm):
        return super().get_form(form_class=form_class)

class ProcessStageUpdateView(ProcessUpdateView):
    model = lgc_models.ProcessStage
    success_message = _('Process stage successfully updated')
    success_url = 'lgc-process-stage'
    title = _('Process Stage')
    delete_url = 'lgc-process-stage-delete'

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

def get_account_layout(layout, new_token, is_hr=False, is_active=False):
    div = Div(css_class='form-row');

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
            HTML(' <a href="{% url "lgc-user-delete" ' + str(uid) +
                 '%}" class="btn btn-outline-danger">' + delete_str + '</a>')
        )
    return form

def get_hr_account_form(form, action, uid, new_token=False, show_tabs=True):
    form.helper = FormHelper()
    if show_tabs:
        form.helper.layout = Layout(TabHolder(
            Tab(_('Information'), get_account_layout(Layout(), new_token,
                                                     True, uid)),
            Tab(_('Employees'),
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
            HTML(' <a href="{% url "lgc-user-delete" ' + str(uid) +
                 '%}" class="btn btn-outline-danger">' + delete_str + '</a>')
        )

    return form

class AccountView(LoginRequiredMixin):
    fields = '__all__'
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

class InitiateAccount(AccountView, SuccessMessageMixin, CreateView):
    success_message = _('New account successfully initiated')
    title = _('Initiate a case')
    form_name = _('Initiate case')
    fields = ['first_name', 'last_name', 'email'];

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

    def test_func(self):
        return True

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
    fields = ['first_name', 'last_name', 'email'];
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

        if self.request.POST:
            context['formset'] = EmployeeFormSet(self.request.POST)
        else:
            init = []
            for p in self.object.hr_employees.all():
                if p.role != user_models.EMPLOYEE:
                    print("employee cannot have an HR role")
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

    def test_func(self):
        obj = self.get_object()
        if obj.role not in user_models.get_hr_roles():
            return False
        return True

class HRAccountListView(HRView, Accounts):
    title = _('HR accounts')
    template_name = 'lgc/accounts.html'
    ajax_search_url = reverse_lazy('lgc-hr-user-search-ajax')
    search_url = reverse_lazy('lgc-hr-accounts')
    users = user_models.get_hr_user_queryset()

class HRDeleteView(HRView, DeleteAccount):
    success_url = reverse_lazy('lgc-hrs')
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
