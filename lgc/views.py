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
from .models import Person
from .forms import PersonCreateForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, Button
from crispy_forms.bootstrap import (
    Accordion, AccordionGroup, Alert, AppendedText, FieldWithButtons,
    InlineCheckboxes, InlineRadios, PrependedAppendedText, PrependedText,
    StrictButton, Tab, TabHolder
)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Files")
        return context

class PersonCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Person
    fields = '__all__'
    success_message = _("File successfully created")

    def get_success_url(self):
        return reverse_lazy('lgc-file', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update'] = False
        context['title'] = _("New File")
        return context

    def get_form(self, form_class=None):
        form = super().get_form(PersonCreateForm)
        form.helper = FormHelper()
        form.helper.add_input(Submit('submit', 'Create',
                                     css_class='btn-primary'))
        form.helper.layout = Layout(
            TabHolder(
                Tab(
                    'Information',
                    Div(
                        'first_name', 'last_name', 'email'),
                    Div('foreigner_id', 'birth_date', 'citizenship', 'passeport_expiry', 'passeport_nationality', 'home_entity', 'home_entity_addr', 'host_entity', 'host_entity_addr')
                ),
                Tab(
                    'tempo',
                    'work_authorization', 'work_authorization_start', 'work_authorization_end', 'residence_permit_start', 'residence_permit_end'
                )
            ),
        )
        return form

class PersonUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Person
    fields = '__all__'
    success_url = reverse_lazy('lgc-files')
    success_message = _("File successfully updated")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update'] = True
        context['title'] = _("File")
        return context

    #def get_form(self, form_class=None):
    #    form = super().get_form(PersonCreateForm)
    #    form.helper = FormHelper()
    #    form.helper.layout = Layout(
    #        TabHolder(
    #            Tab(
    #                'Information',
    #                Div(css_class="fluid",
    #                Div('first_name', 'last_name', 'email', css_class="form-row"),
    #                Div('foreigner_id', 'birth_date', 'citizenship', 'passeport_expiry', 'passeport_nationality', 'home_entity', 'home_entity_addr', 'host_entity', 'host_entity_addr'))
    #            ),
    #            Tab(
    #                'tempo',
    #                'work_authorization', 'work_authorization_start', 'work_authorization_end', 'residence_permit_start', 'residence_permit_end'
    #            )
    #        ),
    #    )
    #    return form

class PersonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Person
    template_name = 'lgc/person_confirm_delete.html'
    success_url = reverse_lazy('lgc-files')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Delete User")
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_message = _("File %s deleted successfully.")%(self.object.id)
        messages.success(self.request, success_message)
        return super().delete(request, *args, **kwargs)

@login_required
def file_create(request):
    context['title'] = _("New File")

    if request.method == 'POST':
        p_form = PersonCreateForm(request.POST)
        c_form = ChildForm(request.POST)

        if p_form.is_valid() and c_form.is_valid():
            user = u_form.save()
            profile = p_form.save(commit=False)
            profile.user = user
            profile.save()
            username = u_form.cleaned_data.get('username')
            messages.success(request,
                             _('The account for %(username)s has been created') %
                             { 'username': username})
            return redirect('lgc-user-create')
        context['u_form'] = u_form
        context['p_form'] = p_form
        return render(request, 'users/create.html', context)
    context['u_form'] = UserCreateForm()
    context['p_form'] = ProfileCreateForm()

    return render(request, 'lgc/file.html', context)
