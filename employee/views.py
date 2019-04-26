import pdb                # pdb.set_trace()
from django.db import transaction
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from common.utils import pagination, lgc_send_email, must_be_staff
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
from lgc import models as lgc_models, views as lgc_views
from . import forms as employee_forms
from lgc.forms import LgcTab
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
from . import models as employee_models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from common import lgc_types
import string
import random
import datetime
import os, pdb

User = get_user_model()

class PersonUpdateView(lgc_views.PersonUpdateView):
    model = employee_models.Employee

    def get_success_url(self):
        return reverse_lazy('employee-file')

def my_file(request):
    if not hasattr(request.user, 'employee_user_set'):
        employee = employee_models.Employee()
        employee.first_name = request.user.first_name
        employee.last_name = request.user.last_name
        employee.email = request.user.email
        employee.user = request.user
        employee.modified_by = request.user
        employee.save()
    view = PersonUpdateView.as_view()
    return view(request, pk=request.user.employee_user_set.id)

@login_required
def my_expirations(request):
    if request.user.role != user_models.EMPLOYEE:
        return http.HttpResponseForbidden()

    form = lgc_views.get_expirations_form(request)

    """ remove the user field """
    del form.fields['user']
    form.helper.layout[0].pop(0)

    objs = lgc_models.Expiration.objects.filter(person=request.user.person_user_set)
    objs = lgc_views.expirations_filter_objs(request, objs)
    return lgc_views.__expirations(request, form, objs)

