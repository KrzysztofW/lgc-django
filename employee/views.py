import pdb                # pdb.set_trace()
from django.db import transaction
from django import forms
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from common.utils import pagination, lgc_send_email, must_be_staff, get_template
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
from django.utils.safestring import mark_safe

from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  DeleteView)
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from lgc import models as lgc_models, views as lgc_views
from . import forms as employee_forms
from lgc import forms as lgc_forms
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
import os
import logging

log = logging.getLogger('employee')

User = get_user_model()
CURRENT_DIR = Path(__file__).parent

class PersonUpdateView(lgc_views.PersonUpdateView):
    model = employee_models.Employee

    def get_success_url(self):
        return reverse_lazy('employee-file')

@login_required
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
    if request.user.role != user_models.ROLE_EMPLOYEE:
        return http.HttpResponseForbidden()

    form = lgc_views.get_expirations_form(request, show_expiry_type=False)

    """ remove the user field """
    del form.fields['user']
    form.helper.layout[0].pop(0)

    objs = lgc_models.Expiration.objects.filter(person=request.user.person_user_set)
    objs = lgc_views.expirations_filter_objs(request, objs)
    return lgc_views.__expirations(request, form, objs)

def paginate_moderations(request, object_list):
    paginate = request.GET.get('paginate', 10)
    order_by = request.GET.get('order_by', 'id')
    object_list = object_list.order_by(order_by)
    paginator = Paginator(object_list, paginate)
    page = request.GET.get('page')
    return paginator.get_page(page)

@login_required
def moderations(request):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    context = {
        'title': 'Moderations',
    }
    context = pagination(request, context, reverse_lazy('employee-moderations'))
    objs = employee_models.Employee.objects.filter(updated=True)
    context['page_obj'] = paginate_moderations(request, objs)

    if (len(objs) and (context['page_obj'].has_next() or
                       context['page_obj'].has_previous())):
        context['is_paginated'] = True
    else:
        context['is_paginated'] = False
    context['header_values'] = [('id', 'ID'), ('first_name', _('First name')),
                                ('last_name', _('Last name')),
                                ('email', _('E-mail')),
                                ('host_entity', _('Host entity'))]
    context['object_list'] = context['page_obj'].object_list
    context['dont_show_search_bar'] = True
    context['item_url'] = 'employee-moderation'

    return render(request, 'lgc/sub_generic_list.html', context)

def objs_diff(objs1, objs2):
    if len(objs1) != len(objs2):
        return True

    for i in range(len(objs1)):
        for key in objs1[i].__dict__.keys():
            if key == '_state' or key == 'id' or key == 'person_id':
                continue
            try:
                obj1_val = getattr(objs1[i], key)
                obj2_val = getattr(objs2[i], key)
            except:
                continue
            if obj1_val != obj2_val:
                return True
    return False

def set_modifiedby_err_msg(request, first_name, last_name, url):
    msg = _('The form has been modified by %(firstname)s %(lastname)s while you were editing it. <a href="%(url)s">Reload the page</a> to continue (your modifications will be lost).')%{
        'firstname':first_name,
        'lastname': last_name,
        'url': url,
    }
    messages.error(request, mark_safe(msg))

def set_formset(request, context, form_class, queryset, person_objs, title,
                prefix, id):
    if request.method == 'POST':
        formset = form_class(request.POST, prefix=prefix)
        if not formset.is_valid():
            raise Exception('Invalid formset')
    else:
        formset = form_class(queryset=queryset, prefix=prefix)
        for form in formset.forms:
            if (hasattr(form.instance, 'expiration') and
                form.instance.expiration):
                form.fields['dcem_end_date'].initial = form.instance.expiration.end_date
                form.fields['dcem_enabled'].initial = form.instance.expiration.enabled

    pcv = lgc_views.PersonCommonView()
    formset.db_objs = pcv.get_formset_objs(person_objs, show_dcem=True)
    formset.title = title
    formset.id = id
    context['formsets'].append(formset)

def get_moderation_object(**kwargs):
    pk = kwargs.get('pk', '')
    if pk == '':
        raise Http404

    obj = employee_models.Employee.objects.filter(id=pk)
    if obj == None or len(obj) != 1:
        raise Http404
    return obj[0]

def set_formsets_form(context):
    formsets_form = forms.Form()
    formsets_form.helper = FormHelper()
    formsets_form.helper.form_tag = False
    formsets_form.helper.layout = Layout(
        Div(Div(HTML(get_template(CURRENT_DIR,
                                  'employee/formsets_template.html')),
                css_class='form-group col-md-10'),
            css_class='form-row'))
    context['formsets_form'] = formsets_form

def check_form(request, context, obj, employee_form, url):
    person_version = obj.user.person_user_set.version
    try:
        person_form_version = int(request.POST.get('pers-version', '0'))
    except:
        person_form_version = None
    employee_version = obj.version

    if person_form_version == None or not employee_form.is_valid():
        return False

    for formset in context['formsets']:
        if not formset.is_valid():
            messages.error(request, _('Invalid %(title)s table.')%{
                'title':formset.title})
            return False

    if person_form_version != person_version:
        set_modifiedby_err_msg(request,
                               obj.user.person_user_set.modified_by.first_name,
                               obj.user.person_user_set.modified_by.last_name,
                               url)
        return False

    if employee_form.cleaned_data['version'] != employee_version:
        set_modifiedby_err_msg(request, obj.modified_by.first_name,
                               obj.modified_by.last_name, url)
        return False

    return True

def save_employee_obj(request, employee_instance):
    employee_instance.version += 1
    employee_instance.updated = False
    employee_instance.modified_by = request.user
    employee_instance.modification_date = timezone.now()
    employee_instance.save()

def save_formset(employee_obj, formset):
    if formset == None:
        return

    for form in formset.forms:
        if len(form.cleaned_data) == 0:
            continue

        if (form.cleaned_data['DELETE'] and
            form.instance.person_child):

            form.instance.person_child.delete()
            form.instance.person_child = None
            expiration = form.instance.expiration
            form.instance.delete()
            expiration.delete()
            continue

        if form.instance.person_child == None:
            person_child = lgc_models.Child()
        else:
            person_child = form.instance.person_child
        person_common_view = lgc_views.PersonCommonView()
        person_common_view.copy_related_object(form.instance,
                                               person_child,
                                               form.instance)
        form.instance.person = employee_obj
        person_child.person = employee_obj.user.person_user_set

        if form.cleaned_data['dcem_end_date']:
            if form.instance.expiration == None:
                expiration = lgc_models.Expiration()
            else:
                expiration = form.instance.expiration
            expiration.end_date = form.cleaned_data['dcem_end_date']
            expiration.enabled = form.cleaned_data['dcem_enabled']
            expiration.person = person_child.person
            expiration.save()
            form.instance.expiration = expiration
        elif form.instance.expiration:
            expiration = form.instance.expiration
            form.instance.expiration = None
            form.instance.person_child.expiration = None
            expiration.delete()

        person_child.expiration = form.instance.expiration
        person_child.save()
        form.instance.person_child = person_child
        form.instance.save()

def handle_docs_formset(request, docs, employee_obj):
    if not docs:
        return 0

    for doc_form in docs.forms:
        try:
            doc = lgc_models.Document.objects.get(id=doc_form.instance.id)
        except:
            messages.error(request, _('Moderation failed.'))
            log.error('moderation of employee %d failed', employee_obj.id)
            return -1

        if ((not doc_form.cleaned_data['reject'] and doc.deleted)
            or
            (doc_form.cleaned_data['reject'] and doc.added)):
            try:
                lgc_models.delete_person_doc(employee_obj.user.person_user_set,
                                             doc_form.instance)
            except Exception as e:
                log.error(e)
                messages.error(request, _('Cannot remove user files.'))
        else:
            doc_form.save()
    return 0

@login_required
def moderation(request, *args, **kwargs):
    if request.user.role not in user_models.get_internal_roles():
        return http.HttpResponseForbidden()

    employee_obj = get_moderation_object(**kwargs)
    formsets = []
    person_form = employee_forms.ModerationPersonCreateForm(instance=employee_obj.user.person_user_set,
                                                            prefix='pers')
    person_form.helper = FormHelper()
    person_form.helper.form_tag = False

    pchildren = lgc_models.Child.objects.filter(person=employee_obj.user.person_user_set).all()

    this_url = str(reverse_lazy('employee-moderation', kwargs={'pk':employee_obj.id}))
    ChildrenFormSet = modelformset_factory(employee_models.Child,
                                           form=employee_forms.ChildCreateForm2,
                                           can_delete=True)
    DocumentFormSet = modelformset_factory(lgc_models.Document,
                                           form=employee_forms.DocumentFormSet,
                                           can_delete=False, extra=0)

    context = {
        'title': 'Moderation', 'person_form': person_form, 'object': employee_obj,
        'formsets': [], 'formsets_form': None,
    }
    person_common_view = lgc_views.PersonCommonView()

    if request.GET.get('reject') == '1':
        person_common_view.copy_related_object(employee_obj.user.person_user_set,
                                               employee_obj, employee_obj)
        save_employee_obj(request, employee_obj)

        person_common_view.clear_related_objects(employee_obj.employee_child_set.all())
        for child in employee_obj.user.person_user_set.child_set.all():
            emp_child = employee_models.Child()
            person_common_view.copy_related_object(child, emp_child, emp_child)
            emp_child.person = employee_obj
            emp_child.person_child = child
            emp_child.save()

        for doc in employee_obj.user.person_user_set.document_set.all():
            if doc.deleted:
                doc.deleted = False
                doc.save()
            elif doc.added:
                try:
                    lgc_models.delete_person_doc(employee_obj.user.person_user_set, doc)
                except Exception as e:
                    log.error(e)
                    messages.error(self.request, _('Cannot remove user files.'))

        messages.success(request, _('Moderation has been rejected.'))
        return redirect('employee-moderations')

    if request.method == 'POST':
        employee_form = (
            employee_forms.ModerationEmployeeUpdateForm(request.POST,
                                                        instance=employee_obj,
                                                        prefix='emp')
        )
        employee_form.helper = FormHelper()
        employee_form.helper.form_tag = False
        context['employee_form'] = employee_form

        docs = None
        valid = True
        if request.POST.get('docs-TOTAL_FORMS'):
            docs = DocumentFormSet(request.POST, prefix='docs')
            if not docs.is_valid():
                messages.error(request, _('Invalid document form.'))
                valid = False

        if request.POST.get('children-TOTAL_FORMS'):
            try:
                set_formset(request, context, ChildrenFormSet, None, pchildren,
                            _('Children'), 'children', 'children_id')
            except:
                messages.error(request, _('Invalid children form'))
                valid = False
            set_formsets_form(context)

        if not check_form(request, context, employee_obj, employee_form, this_url):
            messages.error(request, _('Invalid form.'))
            valid = False

        if valid:
            if len(context['formsets']):
                formset = context['formsets'][0]
            else:
                formset = None

            if handle_docs_formset(request, docs, employee_obj) < 0:
                return redirect('employee-moderations')

            old_person = lgc_models.Person()
            lgc_models.copy_doc_path_attributes(employee_obj.user.person_user_set,
                                                old_person)

            person_common_view.copy_related_object(employee_form.instance,
                                                   employee_obj.user.person_user_set,
                                                   employee_form.instance)
            employee_obj.user.person_user_set.version += 1

            with transaction.atomic():
                save_employee_obj(request, employee_form.instance)
                lgc_models.rename_person_doc_dir(old_person,
                                                 employee_obj.user.person_user_set)
                employee_obj.user.first_name = employee_form.instance.first_name
                employee_obj.user.last_name = employee_form.instance.last_name
                employee_obj.user.save()
                employee_obj.user.person_user_set.save()
                save_formset(employee_obj, formset)

            messages.success(request, _('Moderation successfully submitted.'))
            return redirect('employee-moderations')

    employee_form = employee_forms.ModerationEmployeeUpdateForm(instance=employee_obj,
                                                                prefix='emp')
    employee_form.helper = FormHelper()
    employee_form.helper.form_tag = False
    doc_qs = lgc_models.Document.objects.filter(person=employee_obj.user.person_user_set)
    doc_qs = doc_qs.filter(added=True)|doc_qs.filter(deleted=True)

    if len(doc_qs):
        context['docs'] = DocumentFormSet(queryset=doc_qs, prefix='docs')
        context['doc_download_url'] = 'lgc-download-file'

    echildren = employee_models.Child.objects.filter(person=employee_obj)
    if objs_diff(echildren.all(), pchildren):
        set_formset(request, context, ChildrenFormSet, echildren,
                    pchildren, _('Children'), 'children', 'children_id')
        set_formsets_form(context)

    context['employee_form'] = employee_form
    return render(request, 'employee/moderation.html', context)
