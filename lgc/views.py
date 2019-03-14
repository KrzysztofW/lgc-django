from django.db import transaction
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from common.utils import pagination, lgc_send_email, must_be_staff
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
from .models import Person, ProcessType, Child, ModerationChild
from .forms import (PersonCreateForm, ChildCreateForm, ModerationChildCreateForm,
                    InitiateAccountForm, InitiateHRForm, HREmployeeForm, ProcessForm)
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

User = get_user_model()
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
        return Person.objects.order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Files')
        context['create_url'] = reverse_lazy('lgc-file-create')
        context['update_url'] = 'lgc-file'
        context['show_id'] = True
        context['show_birth_date'] = True

        return pagination(self, context, reverse_lazy('lgc-files'))

def get_template(name):
    try:
        with Path(CURRENT_DIR, 'templates', 'lgc', name).open() as fh:
            return fh.read()
    except FileNotFoundError:
        raise Http404

def get_person_form_layout(form, action):
    form.helper = FormHelper()
    layout = Layout(
        TabHolder(
            Tab(_('Information'),
                Div(Div('first_name', css_class='form-group col-md-4'),
                    Div('last_name', css_class='form-group col-md-4'),
                    css_class='form-row'),
                Div(Div('email', css_class='form-group col-md-4'),
                    Div('citizenship', css_class='form-group col-md-4'),
                    css_class='form-row'),
                Div(Div('foreigner_id', css_class='form-group col-md-4'),
                    Div('birth_date', css_class='form-group col-md-4'),
                    css_class='form-row'),
                Div(Div('process', css_class='form-group col-md-4'),
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
                Div(Div('HR', css_class='form-group col-md-4'),
                    css_class='form-row'),
                Div(Div(HTML(get_template('formset_template.html')),
                        css_class='form-group col-md-10'), css_class='form-row'),
            ),
            Tab(_('Process'),
                #Div(Div(HTML('{% load crispy_forms_tags %}{{ process|crispy }}')),
                #        css_class='form-group col-md-4'),
                #    css_class='form-row'),
                Div(Div('process_name', css_class='form-group col-md-4'),
                    css_class='form-row'),
            ),
            Tab(_('Billing'),
            ),
        )
    )
    layout.append(HTML('<button class="btn btn-outline-info" type="submit">' + action + '</button>'))
    form.helper.layout = layout
    return form

def hr_add_employee(form_data, person_object):
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
        h.hr_employees.add(person_object.id)
        h.save()

class PersonCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Person
    fields = '__all__'
    success_message = _('File successfully created')

    def get_success_url(self):
        return reverse_lazy('lgc-file', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('New File')
        context['formset_title'] = _('Children')
        context['formset_add_text'] = _('Add a child')
        context['process'] = ProcessForm()
        # We cannot use modelformset_factory with Child class as it would
        # get ALL the children from the DB in an empty creation form!
        ChildrenFormSet = formset_factory(form=ChildCreateForm, extra=1,
                                          can_delete=True)

        if self.request.POST:
            context['formset'] = ChildrenFormSet(self.request.POST)
        else:
            context['formset'] = ChildrenFormSet()
        return context

    def form_valid(self, form):
        ChildrenFormSet = modelformset_factory(Child, form=ChildCreateForm,
                                               can_delete=True)
        form.instance.modified_by = self.request.user
        children = ChildrenFormSet(self.request.POST)

        with transaction.atomic():
            self.object = form.save()
            if children.is_valid():
                instances = children.save(commit=False)
                for i in instances:
                    i.parent_id = self.object.id
                    i.save()
                hr_add_employee(form.cleaned_data, self.object)
            else:
                messages.error(self.request, _('Invalid Children table'))
                return super().form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('There are errors on the page'))
        return super().form_invalid(form)

    def get_form(self, form_class=PersonCreateForm):
        form = super().get_form(form_class=form_class)
        return get_person_form_layout(form, _('Create'))

# XXX allow to insert to pending accounts
class PersonUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Person
    child_form = ChildCreateForm
    fields = '__all__'
    success_message = _('File successfully updated')

    def get_success_url(self):
        return reverse_lazy('lgc-file', kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('File')
        context['formset_title'] = _('Children')
        context['formset_add_text'] = _('Add a child')
        ChildrenFormSet = modelformset_factory(Child, self.child_form,
                                               extra=1, can_delete=True)

        if self.request.POST:
            context['formset'] = ChildrenFormSet(self.request.POST)
        else:
            context['formset'] = ChildrenFormSet(queryset=Child.objects.filter(parent=self.object.id))
        context['form'].fields['HR'].initial = self.object.hr_set.all()
        context['form'].fields['process_name'].initial = self.object.processtype_set.all()
        return context

    def get_form(self, form_class=PersonCreateForm):
        form = super().get_form(form_class)
        form = get_person_form_layout(form, _('Update'))

        if self.request.user.is_staff:
            form.helper.layout.append(HTML(' <a href="{% url "lgc-file-delete" object.id %}" class="btn btn-outline-danger">' + _('Delete') + '</a>'))
        return form

    def form_valid(self, form):
        # need to call get_context_data() in order to fill
        # the context['formset'] with POST response
        context = self.get_context_data()
        children = context['formset']
        form.instance.modified_by = self.request.user

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
                hr_add_employee(form.cleaned_data, self.object)
            else:
                messages.error(self.request, _('Invalid Children table'))
                return super().form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('There are errors on the page'))
        return super().form_invalid(form)

class PersonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Person
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
                lgc_send_email(self.object, 'update')
            except Exception as e:
                messages.error(self.request, _('Cannot send email to') + '`'
                               + self.object.email + '`: ' + str(e))
                return super().form_invalid(form)
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
        context['title'] = _('Processes')
        return pagination(self, context, reverse_lazy('lgc-processes'))

class ProcessCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ProcessType
    fields = ['id', 'name']
    success_message = _('Process successfully created')
    template_name = 'lgc/process_form.html'
    success_url = reverse_lazy('lgc-process-create')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update'] = False
        context['title'] = _('New Process')
        return context

class ProcessUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ProcessType
    fields = ['name']
    success_message = _('Process successfully updated')
    template_name = 'lgc/process_form.html'

    def get_success_url(self):
        self.object = self.get_object()
        return reverse_lazy('lgc-process', kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update'] = True
        context['title'] = _('Process')
        return context

class ProcessDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ProcessType
    template_name = 'lgc/process_confirm_delete.html'
    success_url = reverse_lazy('lgc-processes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Process')
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_message = _("Process %s deleted successfully.")%(self.object.id)
        messages.success(self.request, success_message)
        return super().delete(request, *args, **kwargs)

def get_account_layout(layout, new_token, is_hr=False):
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

    if new_token or is_hr:
        row_div = Div(css_class='form-row')
        if new_token:
            row_div.append(Div('new_token', css_class='form-group col-md-4'))
        if is_hr:
            row_div.append(Div('is_admin', css_class='form-group col-md-4'))
        layout.append(row_div)
    return layout

def get_account_form(form, action, new_token=False):
    form.helper = FormHelper()
    form.helper.layout = get_account_layout(Layout(), new_token, False)

    form.helper.layout.append(
        HTML('<button class="btn btn-outline-info" type="submit">' +
             action + '</button>'))
    return form

def get_hr_account_form(form, action, new_token=False, show_tabs=True):
    form.helper = FormHelper()
    if show_tabs:
        form.helper.layout = Layout(TabHolder(
            Tab(_('Information'), get_account_layout(Layout(), new_token,
                                                     is_hr=True)),
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
    return form

class AccountView(LoginRequiredMixin):
    fields = '__all__'
    template_name = 'lgc/person_form.html'
    model = User
    success_url = 'lgc-account'
    delete_url = 'lgc-account-delete'
    create_url = reverse_lazy('lgc-account-create')
    update_url = 'lgc-account'
    cancel_url = 'lgc-account'
    list_url = reverse_lazy('lgc-accounts')
    form_class = InitiateAccountForm
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
        return context

    def get_form(self, form_class=InitiateAccountForm):
        form = super().get_form(form_class=self.form_class)
        if self.is_hr:
            return get_hr_account_form(form, self.form_name, True, False)
        return get_account_form(form, self.form_name, True)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        form.cleaned_data['new_token'] = True

        if self.is_hr:
            if form.cleaned_data['is_admin']:
                form.instance.role = user_models.HR_ADMIN
            else:
                form.instance.role = user_models.HR
        else:
            form.instance.role = user_models.EMPLOYEE
        try:
            lgc_send_email(self.object, 'update')
        except Exception as e:
            messages.error(self.request, _('Cannot send email to') + '`'
                           + self.object.email + '`: ' + str(e))
            return super().form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('There are errors on the page'))
        return super().form_invalid(form)

class PendingAccounts(AccountView, PersonCommonListView, UserPassesTestMixin):
    title = _('Pending Accounts')
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
        users = user_models.get_employee_user_queryset()
        return users.filter(GDPR_accepted=None).order_by('-id')

class UpdatePendingAccount(AccountView, SuccessMessageMixin, UpdateView):
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
        return context

    def get_form(self, form_class=InitiateAccountForm):
        form = super().get_form(form_class=self.form_class)

        if self.is_hr:
            return get_hr_account_form(form, self.form_name, True, True)
        return get_account_form(form, self.form_name, True)

    def form_valid(self, form, relations = None):
        self.object = form.save(commit=False)

        if self.is_hr:
            if form.cleaned_data['is_admin']:
                form.instance.role = user_models.HR_ADMIN
            else:
                form.instance.role = user_models.HR
        else:
            form.instance.role = user_models.EMPLOYEE

        try:
            lgc_send_email(self.object, 'update')
        except Exception as e:
            messages.error(self.request, _('Cannot send email to') + '`'
                           + self.object.email + '`: ' + str(e))
            return super().form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('There are errors on the page'))
        return super().form_invalid(form)

class DeletePendingAccount(AccountView, PersonDeleteView):
    obj_name = _('Pending account')
    title = _('Delete Pending Account')
    success_url = reverse_lazy('lgc-accounts')
    template_name = 'lgc/person_confirm_delete.html'

class HRView(LoginRequiredMixin):
    req_type = ReqType.HR
    template_name = 'lgc/person_form.html'
    model = User
    success_url = 'lgc-hr'
    delete_url = 'lgc-hr-delete'
    create_url = reverse_lazy('lgc-hr-create')
    update_url = 'lgc-hr'
    cancel_url = 'lgc-hr'
    list_url = reverse_lazy('lgc-hrs')
    form_class = InitiateHRForm
    is_hr = True

    class Meta:
        abstract = True

class HRCreateView(HRView, InitiateAccount):
    success_message = _('New HR account successfully initiated')
    title = _('New HR account')
    form_name = _('Initiate account')

class HRUpdateView(HRView, UpdatePendingAccount):
    success_message = _('HR account successfully updated')
    title = _('Update HR')

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
            for p in self.object.hr_employees.all():
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
        for f in employees.cleaned_data:
            if not 'id' in f:
                continue
            if self.is_deleted(employees, f['id']):
                continue
            e = users.filter(id=f['id'])
            if e == None:
                messages.error(self.request, _("Unknown file ID `%s'"%(f['id'])))
                return super().form_invalid(form)
            e = e.get()
            if e == None:
                messages.error(self.request, _("Unknown file ID `%s'"%(f['id'])))
                return super().form_invalid(form)
            if e.email == None:
                messages.error(self.request, _("Employee's e-mail cannot be empty in file `%s'"%(f['id'])))
                return super().form_invalid(form)
            self.object.hr_employees.add(e)
        self.object.save()
        #return self.render_to_response(self.get_context_data(form=form))
        return super().form_valid(form, self.object.hr_employees.all())

class HRAccountListView(HRView, PendingAccounts):
    title = _('Pending HR accounts')
    template_name = 'lgc/person_list.html'

    def get_queryset(self):
        users = user_models.get_hr_user_queryset()
        objs = users.filter(GDPR_accepted=None)|users.filter(GDPR_accepted=False)
        return objs.order_by('-id')

class HRListView(HRView, PendingAccounts):
    title = _('Human resources')
    template_name = 'lgc/person_list.html'

    def get_queryset(self):
        users = user_models.get_hr_user_queryset()
        return users.filter(GDPR_accepted=True).order_by('-id')

class HRDeleteView(HRView, DeletePendingAccount):
    success_url = reverse_lazy('lgc-hrs')
    obj_name = _('Pending HR account')
    title = _('Delete Pending HR account')
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
