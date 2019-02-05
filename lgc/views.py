from django.db import transaction
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from common.utils import pagination
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
from .models import Person, ProcessType, Child, Employee, EmployeeChild, HR
from .forms import (PersonCreateForm, ChildCreateForm, EmployeeCreateForm,
                    EmployeeChildCreateForm)
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

class PersonListView(LoginRequiredMixin, ListView):
    template_name = 'lgc/person_list.html'
    model = Person
    fields = '__all__'
    context_object_name = 'persons'

    def test_func(self):
        return self.request.user.is_staff

    def get_ordering(self):
        return self.request.GET.get('order_by', 'id')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Files")
        context['create_url'] = reverse_lazy('lgc-file-create')
        context['update_url'] = '/file/'
        return pagination(self, context, reverse_lazy('lgc-files'))

def get_children_formset_template(children):
    try:
        with Path(CURRENT_DIR, 'templates', 'lgc', 'children_template.html').open() as fh:
            return fh.read()
    except FileNotFoundError:
        raise Http404

def get_process_layout():
    pass

def get_person_form_layout(action, processes, children):
    html = '<label for="process" class="col-form-label requiredField">'
    html += _('Process') + '<span class="asteriskField">*</span> </label>'
    html += '<select class="form-control form-control-sm">'
    for p in processes:
        html += "<option>" + p.name + "</option>\n"
    html += "</select>"

    return Layout(
        TabHolder(
            Tab('Information',
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
                Div(Div('work_authorization')),
                Div(Div('work_authorization_start', css_class="form-group col-md-4"),
                    Div('work_authorization_end', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div(HTML(get_children_formset_template(children)),
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

def get_employee_form_layout(action, children):
    return Layout(
        Div(Div('first_name', css_class="form-group col-md-4"),
            Div('last_name', css_class="form-group col-md-4"),
            css_class="form-row"),
        Div(Div('email', css_class="form-group col-md-4"),
            css_class="form-row"),
        Div(HTML('<label><b>' + _('Public interface information') + '</b></label>'), css_class="form-row"),
        TabHolder(
            Tab('Information',
                Div(Div('foreigner_id', css_class="form-group col-md-4"),
                    Div('birth_date', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div('citizenship', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div('passeport_expiry', css_class="form-group col-md-4"),
                    Div('passeport_nationality', css_class="form-group col-md-4"),
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
                Div(Div('work_authorization')),
                Div(Div('work_authorization_start', css_class="form-group col-md-4"),
                    Div('work_authorization_end', css_class="form-group col-md-4"),
                    css_class="form-row"),
                Div(Div(HTML(get_children_formset_template(children)),
                        css_class="form-group col-md-10"), css_class="form-row")),
            Tab(_('Process'), get_process_layout())),
        HTML('<button class="btn btn-outline-info" type="submit">' + action + '</button>'))

class PersonCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Person
    child_model = Child
    fields = '__all__'
    success_message = _("File successfully created")

    def get_success_url(self):
        return reverse_lazy('lgc-file', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("New File")
        context['process'] = ProcessType.objects.all()
        # We cannot use modelformset_factory with Child class as it would
        # get ALL the children from the DB in an empty creation form!
        ChildrenFormSet = formset_factory(form=ChildCreateForm, extra=1)

        if self.request.POST:
            context['children'] = ChildrenFormSet(self.request.POST)
        else:
            context['children'] = ChildrenFormSet()
        return context

    def form_valid(self, form):
        ChildrenFormSet = modelformset_factory(self.child_model,
                                               form=ChildCreateForm)

        self.object = form.save()
        children = ChildrenFormSet(self.request.POST)
        with transaction.atomic():
            if children.is_valid():
                instances = children.save(commit=False)
                for i in instances:
                    i.parent_id = self.object.id
                    i.save()
        return super(PersonCreateView, self).form_valid(form)

    def get_form(self, form_class=PersonCreateForm, form_only=False):
        form = super().get_form(form_class=form_class)
        if form_only:
           return form
        ChildrenFormSet = formset_factory(form=ChildCreateForm)
        children = ChildrenFormSet()
        form.helper = FormHelper()
        form.helper.layout = get_person_form_layout(_("Create"),
                                                    ProcessType.objects.all(),
                                                    children)
        return form

class PersonUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Person
    child_model = Child
    child_form = ChildCreateForm
    fields = '__all__'
    success_message = _("File successfully updated")

    def get_success_url(self):
        #object = self.get_object()
        return reverse_lazy('lgc-file', kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("File")
        context['process'] = ProcessType.objects.all()
        ChildrenFormSet = modelformset_factory(self.child_model,
                                               self.child_form,
                                               extra=1, can_delete=True)
        if self.request.POST:
            context['children'] = ChildrenFormSet(self.request.POST)
        else:
            context['children'] = ChildrenFormSet(queryset=self.child_model.objects.filter(parent=self.object.id))
        return context

    def get_form(self, form_class=PersonCreateForm, form_only=False):
        form = super().get_form(form_class)
        if form_only:
            return form
        ChildrenFormSet = formset_factory(form=ChildCreateForm)
        if self.request.POST:
            children = ChildrenFormSet(self.request.POST)
        else:
            children = ChildrenFormSet()
        form.helper = FormHelper()
        form.helper.layout = get_person_form_layout(_("Update"),
                                                    ProcessType.objects.all(), children)
        form.helper.layout.append(HTML(' <a href="{% url "lgc-file-delete" object.id %}" class="btn btn-outline-danger">' + _("Delete") + '</a>'))
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        children = context['children']
        with transaction.atomic():
            if children.is_valid():
                for obj in children.deleted_forms:
                    if (obj.instance.id != None):
                        obj.instance.delete()
                instances = children.save(commit=False)
                for i in instances:
                    i.parent_id = self.object.id
                    i.save()
        return super(PersonUpdateView, self).form_valid(form)

class PersonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Person
    template_name = 'lgc/person_confirm_delete.html'
    success_url = reverse_lazy('lgc-files')
    obj_name = _("File")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Delete File")
        context['cancel_url'] = reverse_lazy('lgc-file', kwargs={'pk':self.object.id})
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        obj_name = kwargs.get('obj_name', _('File'))
        success_message = _("%s of %s %s (ID %s) deleted successfully.")%(self.obj_name, self.object.first_name, self.object.last_name, self.object.id)
        messages.success(self.request, success_message)
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

class EmployeeListView(PersonListView):
    model = Employee

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Employees")
        context['create_url'] = reverse_lazy('lgc-employee-create')
        context['update_url'] = '/employee/'
        return context

class EmployeeCreateView(PersonCreateView):
    model = Employee
    child_model = EmployeeChild
    success_message = _("Employee successfully created")
    template_name = 'lgc/person_form.html'

    def get_success_url(self):
        return reverse_lazy('lgc-employee', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("New Employee")
        return context

    def get_form(self, form_class=EmployeeCreateForm):
        form = super().get_form(form_class=form_class, form_only=True)
        ChildrenFormSet = formset_factory(form=EmployeeChildCreateForm)
        children = ChildrenFormSet()
        form.helper = FormHelper()
        form.helper.layout = get_employee_form_layout(_("Create"), children)
        return form

class EmployeeUpdateView(PersonUpdateView):
    model = Employee
    child_model = EmployeeChild
    child_form = EmployeeChildCreateForm
    success_message = _("Employee successfully updated")
    template_name = 'lgc/person_form.html'

    def get_success_url(self):
        return reverse_lazy('lgc-employee', kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Employee")
        return context

    def get_form(self, form_class=None):
        form = super().get_form(EmployeeCreateForm, True)
        ChildrenFormSet = formset_factory(form=EmployeeChildCreateForm)
        if self.request.POST:
            children = ChildrenFormSet(self.request.POST)
        else:
            children = ChildrenFormSet()
        form.helper = FormHelper()
        form.helper.layout = get_employee_form_layout(_("Update"), children)
        form.helper.layout.append(HTML(' <a href="{% url "lgc-employee-delete" object.id %}" class="btn btn-outline-danger">' + _("Delete") + '</a>'))

        return form

        form = super().get_form(EmployeeCreateForm)
        form.helper.layout.pop(-1)
        form.helper.layout.append(HTML(' <a href="{% url "lgc-employee-delete" object.id %}" class="btn btn-outline-danger">' + _("Delete") + '</a>'))

        return form

class EmployeeDeleteView(PersonDeleteView):
    model = Employee
    success_url = reverse_lazy('lgc-employees')
    obj_name = _("Employee")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Delete Employee")
        context['cancel_url'] = reverse_lazy('lgc-employee', kwargs={'pk':self.object.id})
        return context
