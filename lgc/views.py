from django.db import transaction
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from common.utils import pagination, queue_request, must_be_staff
from common.lgc_types import ReqType, ReqAction
from django import http
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin

from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  DeleteView)
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from .models import Person, ProcessType, Child, ModerationChild, HR
from .forms import (PersonCreateForm, ChildCreateForm, ModerationChildCreateForm,
                    InitiateCaseForm, InitiateHRForm, HREmployeeForm)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, Button, Row, HTML, MultiField
from crispy_forms.bootstrap import (
    Accordion, AccordionGroup, Alert, AppendedText, FieldWithButtons,
    InlineCheckboxes, InlineRadios, PrependedAppendedText, PrependedText,
    StrictButton, Tab, TabHolder
)
from pathlib import Path
from django.http import Http404

CURRENT_DIR = Path(__file__).parent

@login_required
def home(request):
    return render(request, 'lgc/index.html', {'title':'Home'})

@login_required
def tables(request):
    return render(request, 'lgc/tables.html', {'title':'Tables'})

class PersonCommonListView(LoginRequiredMixin, ListView):
    template_name = 'lgc/person_list.html'
    model = Person
    fields = '__all__'
    context_object_name = 'persons'

    class Meta:
        abstract = True

    def get_ordering(self):
        return self.request.GET.get('order_by', '-id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

class PersonListView(PersonCommonListView):
    def get_queryset(self):
        order_by = self.get_ordering()
        return Person.objects.filter(GDPR_accepted=True).order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Files")
        context['create_url'] = reverse_lazy('lgc-file-create')
        context['update_url'] = 'lgc-file'

        return pagination(self, context, reverse_lazy('lgc-files'))

def get_template(name):
    try:
        with Path(CURRENT_DIR, 'templates', 'lgc', name).open() as fh:
            return fh.read()
    except FileNotFoundError:
        raise Http404

def get_process_layout():
    pass

def get_person_form_layout(action, processes):
    html = '<label for="process" class="col-form-label requiredField">'
    html += _('Process') + '<span class="asteriskField">*</span> </label>'
    html += '<select class="form-control form-control-sm">'
    for p in processes:
        html += "<option>" + p.name + "</option>\n"
    html += "</select>"

    return Layout(
        TabHolder(
            Tab(_('Information'),
                Div(Div('first_name', css_class="form-group col-md-4"),
                    Div('last_name', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div('email', css_class="form-group col-md-4"),
                    Div('citizenship', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div('foreigner_id', css_class="form-group col-md-4"),
                    Div('birth_date', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div('process', css_class="form-group col-md-4"),
                    Div('responsible', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div('passport_expiry', css_class="form-group col-md-4"),
                    Div('passport_nationality', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div('home_entity', css_class="form-group col-md-4"),
                    Div('host_entity', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div('home_entity_address', css_class="form-group col-md-4"),
                    Div('host_entity_address', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div('home_entity_country', css_class="form-group col-md-4"),
                    Div('host_entity_country', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div('HR', css_class="form-group col-md-4"),
                    Div('company', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div('work_authorization')),
                Div(Div('work_authorization_start', css_class="form-group col-md-4"),
                    Div('work_authorization_end', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div(HTML(get_template('formset_template.html')),
                        css_class="form-group col-md-10"), css_class="form-row"),
            ),
            Tab(_('Process'),
                Div(Div(HTML(html), css_class="form-group col-md-4"),
                    css_class="form-row"),
            ),
            Tab(_('Billing'),
            ),
        ),
        HTML('<button class="btn btn-outline-info" type="submit">' + action + '</button>'),
    )

def person_add_hr(form_data, person_object):
    person_object.hr_set.clear()

    if 'HR' not in form_data:
        return
    for i in form_data['HR']:
        h = HR.objects.filter(id=i.id)
        if not h:
            return
        h = h.get()
        if not h:
            return
        h.person.add(person_object.id)
        h.save()

class PersonCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Person
    fields = '__all__'
    success_message = _("File successfully created")

    def get_success_url(self):
        return reverse_lazy('lgc-file', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("New File")
        context['formset_title'] = _('Children')
        context['formset_add_text'] = _('Add a child')
        context['process'] = ProcessType.objects.all()
        # We cannot use modelformset_factory with Child class as it would
        # get ALL the children from the DB in an empty creation form!
        ChildrenFormSet = formset_factory(form=ChildCreateForm, extra=1)

        if self.request.POST:
            context['formset'] = ChildrenFormSet(self.request.POST)
        else:
            context['formset'] = ChildrenFormSet()
        return context

    def form_valid(self, form):
        ChildrenFormSet = modelformset_factory(Child, form=ChildCreateForm)

        # force GDPR_accepted = True for manually created files
        form.instance.GDPR_accepted = True

        children = ChildrenFormSet(self.request.POST)
        with transaction.atomic():
            self.object = form.save()
            if children.is_valid():
                instances = children.save(commit=False)
                for i in instances:
                    i.parent_id = self.object.id
                    i.save()
                person_add_hr(form.cleaned_data, self.object)
        return super().form_valid(form)

    def get_form(self, form_class=PersonCreateForm):
        form = super().get_form(form_class=form_class)
        form.helper = FormHelper()
        form.helper.layout = get_person_form_layout(_("Create"),
                                                    ProcessType.objects.all())
        return form

# XXX allow to insert to pending cases
class PersonUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Person
    child_form = ChildCreateForm
    fields = '__all__'
    success_message = _("File successfully updated")

    def get_success_url(self):
        return reverse_lazy('lgc-file', kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("File")
        context['formset_title'] = _('Children')
        context['formset_add_text'] = _('Add a child')
        context['process'] = ProcessType.objects.all()
        ChildrenFormSet = modelformset_factory(Child, self.child_form,
                                               extra=1, can_delete=True)
        if self.request.POST:
            context['formset'] = ChildrenFormSet(self.request.POST)
        else:
            context['formset'] = ChildrenFormSet(queryset=Child.objects.filter(parent=self.object.id))
        context['form'].fields['HR'].initial = self.object.hr_set.all().order_by('company')
        return context

    def get_form(self, form_class=PersonCreateForm):
        form = super().get_form(form_class)
        form.helper = FormHelper()
        form.helper.layout = get_person_form_layout(_("Update"),
                                                    ProcessType.objects.all())
        if self.request.user.is_staff:
            form.helper.layout.append(HTML(' <a href="{% url "lgc-file-delete" object.id %}" class="btn btn-outline-danger">' + _("Delete") + '</a>'))
        return form

    def form_valid(self, form):
        # need to call get_context_data() in order to fill
        # the context['formset'] with POST response
        context = self.get_context_data()
        children = context['formset']

        if not self.request.POST:
            return super().form_valid(form)

        with transaction.atomic():
            if children.is_valid():
                for obj in children.deleted_forms:
                    if (obj.instance.id != None):
                        obj.instance.delete()
                instances = children.save(commit=False)
                for i in instances:
                    i.parent_id = self.object.id
                    i.save()

                person_add_hr(form.cleaned_data, self.object)
            else:
                return super().form_invalid(form)
        return super().form_valid(form)

def gen_form_from_obj(obj, token=False):
    form = {}
    form['first_name'] = obj.first_name
    form['last_name'] = obj.last_name
    form['email'] = obj.email
    form['company'] = obj.company
    form['language'] = 'EN'
    form['new_token'] = token
    form['responsible'] = []
    return form

class PersonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Person
    obj_name = _("File")
    title = _("Delete File")
    template_name = 'lgc/person_confirm_delete.html'
    success_url = reverse_lazy('lgc-files')
    cancel_url = 'lgc-file'
    file_prefix = 'case_'
    req_type = ReqType.CASE

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
            self.request.POST['inform_person'] == "on"):
            token = True
        else:
            token = False
        queue_request(self.req_type, ReqAction.DELETE,
                      self.file_prefix + str(self.object.id),
                      gen_form_from_obj(self.object, token=token))
        return super().delete(request, *args, **kwargs)

class ProcessListView(LoginRequiredMixin, ListView):
    template_name = 'lgc/process_list.html'
    model = ProcessType
    fields = '__all__'
    context_object_name = 'processes'

    def get_ordering(self):
        return self.request.GET.get('order_by', 'id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Processes")
        return pagination(self, context, reverse_lazy('lgc-processes'))

class ProcessCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ProcessType
    fields = ['id', 'name']
    success_message = _("Process successfully created")
    template_name = 'lgc/process_form.html'

    def get_success_url(self):
        return reverse_lazy('lgc-process', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update'] = False
        context['title'] = _("New Process")
        return context

class ProcessUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ProcessType
    fields = ['name']
    success_message = _("File successfully updated")
    template_name = 'lgc/process_form.html'

    def get_success_url(self):
        self.object = self.get_object()
        return reverse_lazy('lgc-process', kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update'] = True
        context['title'] = _("Process")
        return context

class ProcessDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ProcessType
    template_name = 'lgc/process_confirm_delete.html'
    success_url = reverse_lazy('lgc-processes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Delete Process")
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_message = _("Process %s deleted successfully.")%(self.object.id)
        messages.success(self.request, success_message)
        return super().delete(request, *args, **kwargs)

def get_case_layout(layout, new_token, show_is_admin):
    layout.append(
        Div(
            Div('first_name', css_class="form-group col-md-4"),
            Div('last_name', css_class="form-group col-md-4"),
            css_class="form-row"))
    layout.append(
        Div(
            Div('email', css_class="form-group col-md-4"),
            Div('language', css_class="form-group col-md-4"),
            css_class="form-row"))
    layout.append(
        Div(
            Div('company', css_class="form-group col-md-4"),
            Div('responsible', css_class="form-group col-md-4"),
            css_class="form-row"))

    if new_token or show_is_admin:
        row_div = Div(css_class="form-row")
        if new_token:
            row_div.append(Div('new_token', css_class="form-group col-md-4"))
        if show_is_admin:
            row_div.append(Div('is_admin', css_class="form-group col-md-4"))
        layout.append(row_div)
    return layout

def get_case_form(form, action, new_token=False):
    form.helper.layout = get_case_layout(Layout(), new_token, False)

    form.helper.layout.append(
        HTML('<button class="btn btn-outline-info" type="submit">' +
             action + '</button>'))
    return form

def get_hr_case_form(form, action, new_token=False):
    layout = Layout(TabHolder(
        Tab(_('Information'), get_case_layout(Layout(), new_token, True)),
        Tab(_('Employees'),
            Div(Div(HTML(get_template('employee_list.html')),
                    css_class="form-group col-md-10"), css_class="form-row"),),
    ))

    form.helper.layout = layout
    form.helper.layout.append(
        HTML('<button class="btn btn-outline-info" type="submit">' +
             action + '</button>'))
    form.name = "first_form"
    return form

class CaseView(LoginRequiredMixin):
    fields = '__all__'
    req_type = ReqType.CASE
    template_name = 'lgc/person_form.html'
    model = Person
    success_url = 'lgc-case'
    delete_url = "lgc-case-delete"
    create_url = reverse_lazy('lgc-case-create')
    update_url = 'lgc-case'
    cancel_url = 'lgc-case'
    list_url = reverse_lazy('lgc-cases')
    form_class = InitiateCaseForm
    file_prefix = 'case_'

    class Meta:
        abstract = True

class InitiateCase(CaseView, SuccessMessageMixin, CreateView):
    success_message = _("New case successfully initiated")
    title = _("New Case")
    form_name = _("Initiate case")
    fields = ['first_name', 'last_name', 'email'];

    def get_success_url(self):
        return reverse_lazy(self.success_url, kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def get_form(self, form_class=InitiateCaseForm):
        if self.request.method == 'POST':
            self.request.session['case_lang'] = self.request.POST['language']
        form = super().get_form(form_class=self.form_class)
        form.helper = FormHelper()
        return get_case_form(form, self.form_name)

    def form_valid(self, form):
        self.object = form.save()
        form.cleaned_data['new_token'] = True
        queue_request(self.req_type, ReqAction.ADD,
                      self.file_prefix + str(self.object.id),
                      form.cleaned_data)
        return super().form_valid(form)

class PendingCases(CaseView, PersonCommonListView, UserPassesTestMixin):
    title = _("Pending Cases")
    template_name = 'lgc/person_list.html'

    def test_func(self):
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['create_url'] = self.create_url
        context['update_url'] = self.update_url
        return pagination(self, context, self.list_url)

    def get_queryset(self):
        return Person.objects.filter(GDPR_accepted=None).order_by('-id')

class UpdatePendingCase(CaseView, SuccessMessageMixin, UpdateView):
    success_message = _("Case successfully updated")
    fields = ['first_name', 'last_name', 'email'];
    title = _("Update Case")
    form_name = _("Update")
    show_is_admin = False

    def get_success_url(self):
        return reverse_lazy(self.success_url, kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['formset_title'] = _('Employees')
        context['formset_add_text'] = _('Add an employee')

        return context

    def get_form(self, form_class=InitiateCaseForm):
        form = super().get_form(form_class=self.form_class)

        if self.request.method == 'POST' and self.request.POST.get('language'):
            self.request.session['case_lang'] = self.request.POST['language']
        elif 'case_lang' not in self.request.session:
            self.request.session['case_lang'] = ""

        form.initial['language'] = self.request.session['case_lang']
        form.helper = FormHelper()
        if self.show_is_admin:
            return get_hr_case_form(form, self.form_name, True)
        return get_case_form(form, self.form_name, True)

    def form_valid(self, form, relations = None):
        queue_request(self.req_type, ReqAction.UPDATE,
                      self.file_prefix + str(self.object.id),
                      form.cleaned_data, relations)
        return super().form_valid(form)

class DeletePendingCase(CaseView, PersonDeleteView):
    obj_name = _("Pending case")
    title = _("Delete Pending Case")
    success_url = reverse_lazy('lgc-cases')
    template_name = 'lgc/person_confirm_delete.html'

class HRView(LoginRequiredMixin):
    req_type = ReqType.HR
    template_name = 'lgc/person_form.html'
    model = HR
    success_url = 'lgc-hr'
    delete_url = "lgc-hr-delete"
    create_url = reverse_lazy('lgc-hr-create')
    update_url = 'lgc-hr'
    cancel_url = 'lgc-hr'
    list_url = reverse_lazy('lgc-hrs')
    form_class = InitiateHRForm
    file_prefix = 'hr_'
    show_is_admin = True

    class Meta:
        abstract = True

class HRCreateView(HRView, InitiateCase):
    success_message = _("New HR case successfully initiated")
    title = _("New HR case")
    form_name = _("Initiate case")

class HRUpdateView(HRView, UpdatePendingCase):
    success_message = _("HR case successfully updated")
    title = _("Update HR")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset_title'] = ''
        context['formset_add_text'] = _('Add an employee')
        EmployeeFormSet = formset_factory(HREmployeeForm,
                                          extra=0, can_delete=True)

        if self.request.POST:
            context['formset'] = EmployeeFormSet(self.request.POST)
        else:
            init = []
            for p in self.object.person.all():
                init.append({'id':p.id, 'first_name':p.first_name, 'last_name':p.last_name,
                             'company':p.company })
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

        if not form.is_valid() or not employees.is_valid():
            return super().form_invalid(form)

        self.object = form.save()
        self.object.person.clear()
        for f in employees.cleaned_data:
            if not 'id' in f:
                continue
            if self.is_deleted(employees, f['id']):
                continue
            p = Person.objects.filter(id=f['id'])
            if p == None:
                messages.error(self.request, _("Unknown file ID `%s'"%(f['id'])))
                return super().form_invalid(form)
            p = p.get()
            if p == None:
                messages.error(self.request, _("Unknown file ID `%s'"%(f['id'])))
                return super().form_invalid(form)
            if p.email == None:
                messages.error(self.request, _("Employee's e-mail cannot be empty in file `%s'"%(f['id'])))
                return super().form_invalid(form)
            self.object.person.add(p)
        self.object.save()
        return super().form_valid(form, self.object.person.all())

class HRCaseListView(HRView, PendingCases):
    title = _("Pending HR cases")
    template_name = 'lgc/person_list.html'

    def get_queryset(self):
        objs = HR.objects.filter(GDPR_accepted=None)|HR.objects.filter(GDPR_accepted=False)
        return objs.order_by('-id')

class HRListView(HRView, PendingCases):
    title = _("Human resources")
    template_name = 'lgc/person_list.html'

    def get_queryset(self):
        return HR.objects.filter(GDPR_accepted=True).order_by('-id')

class HRDeleteView(HRView, DeletePendingCase):
    success_url = reverse_lazy('lgc-hrs')
    obj_name = _("Pending HR case")
    title = _("Delete Pending HR case")
    template_name = 'lgc/person_confirm_delete.html'

@login_required
@must_be_staff
def ajax_insert_file_view(request):
    term = request.GET.get('term', '')
    files = Person.objects.filter(first_name__istartswith=term)|Person.objects.filter(last_name__istartswith=term)|Person.objects.filter(home_entity__istartswith=term)
    files = files[:10]

    for f in files:
        if term in f.first_name.lower():
            f.b_first_name = f.first_name.lower()
        elif term in f.last_name.lower():
            f.b_last_name = f.last_name.lower()
        elif term in f.home_entity.lower():
            f.b_company = f.home_entity.lower()
        f.company = f.home_entity
    context = {
        'files': files
    }
    return render(request, 'lgc/insert_file.html', context)
