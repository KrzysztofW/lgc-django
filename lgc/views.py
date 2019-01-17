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
from .models import Person, ProcessType, Child
from .forms import PersonCreateForm, ChildCreateForm
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
        return pagination(self, context, reverse_lazy('lgc-files'))

def get_children_formset_template(children):
    try:
        with Path(CURRENT_DIR, 'templates', 'lgc', 'children_template.html').open() as fh:
            return fh.read()
    except FileNotFoundError:
        raise Http404

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
                Div(Div('residence_permit_start', css_class="form-group col-md-4"),
                    Div('residence_permit_end', css_class="form-group col-md-4"),
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

class PersonCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Person
    fields = '__all__'
    success_message = _("File successfully created")

    def get_success_url(self):
        return reverse_lazy('lgc-file', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("New File")
        context['process'] = ProcessType.objects.all()
        # We cannot use modelformset_factory with Child as it would
        # get ALL the children from the DB in an empty creation form!
        ChildrenFormSet = formset_factory(form=ChildCreateForm, extra=1)

        if self.request.POST:
            context['children'] = ChildrenFormSet(self.request.POST)
        else:
            context['children'] = ChildrenFormSet()
        return context

    def form_valid(self, form):
        ChildrenFormSet = modelformset_factory(Child, form=ChildCreateForm)

        self.object = form.save()
        children = ChildrenFormSet(self.request.POST)
        with transaction.atomic():
            if children.is_valid():
                instances = children.save(commit=False)
                for i in instances:
                    i.person_id = self.object.id
                    i.save()
        return super(PersonCreateView, self).form_valid(form)

    def get_form(self, form_class=None):
        ChildrenFormSet = formset_factory(form=ChildCreateForm)
        children = ChildrenFormSet()
        form = super().get_form(PersonCreateForm)
        form.helper = FormHelper()
        form.helper.layout = get_person_form_layout(_("Create"),
                                                    ProcessType.objects.all(),
                                                    children)
        return form

class PersonUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Person
    fields = '__all__'
    success_message = _("File successfully updated")

    def get_success_url(self):
        #object = self.get_object()
        return reverse_lazy('lgc-file', kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("File")
        context['process'] = ProcessType.objects.all()
        ChildrenFormSet = modelformset_factory(Child, form=ChildCreateForm, extra=1, can_delete=True)
        if self.request.POST:
            context['children'] = ChildrenFormSet(self.request.POST)
        else:
            context['children'] = ChildrenFormSet(queryset=Child.objects.filter(person=self.object.id))
        return context

    def get_form(self, form_class=None):
        form = super().get_form(PersonCreateForm)
        ChildrenFormSet = formset_factory(form=ChildCreateForm)
        if self.request.POST:
            formset = ChildrenFormSet(self.request.POST)
        else:
            formset = ChildrenFormSet()
        form.helper = FormHelper()
        form.helper.layout = get_person_form_layout(_("Update"),
                                                    ProcessType.objects.all(), formset)
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
                    i.person_id = self.object.id
                    i.save()
        return super(PersonUpdateView, self).form_valid(form)

class PersonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Person
    template_name = 'lgc/person_confirm_delete.html'
    success_url = reverse_lazy('lgc-files')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Delete File")
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_message = _("File of %s %s (ID %s) deleted successfully.")%(self.object.first_name, self.object.last_name, self.object.id)
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
