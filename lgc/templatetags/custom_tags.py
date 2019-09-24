from django import template
from users import models as user_models
from lgc import models as lgc_models
from employee import models as employee_models
from lgc import views as lgc_views
from django.conf import settings
from django.utils import timezone
from django.utils.text import Truncator
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from django.template.defaultfilters import date, time
from common.session_cache import session_cache_add, session_cache_get
import datetime

User = get_user_model()
register = template.Library()

@register.simple_tag
def get_notification_menu(request):
    res = {}
    compare_date = timezone.now().date() + datetime.timedelta(days=settings.EXPIRATIONS_NB_DAYS)
    expirations = lgc_models.Expiration.objects.filter(person__responsible=request.user, enabled=True, end_date__lte=compare_date).order_by('end_date').exclude(end_date__lte=timezone.now().date())
    deletion_requests = User.objects.filter(status__in=user_models.get_user_deleted_statuses())
    res['expirations'] = expirations[:10]
    res['deletion_requests'] = deletion_requests[:5]
    res['today'] = timezone.now().date()
    res['pcnt'] = 0

    if request.user.role == user_models.ROLE_CONSULTANT:
        processes = lgc_models.PersonProcess.objects.filter(person__responsible=request.user, invoice_alert=True)

        res['ready_to_invoice'] = processes
        res['pcnt'] += processes.count()

    res['nb_items'] = len(expirations) + len(deletion_requests) + res['pcnt']
    if request.user.billing and request.user.show_invoice_notifs:
        invoices = lgc_models.Invoice.objects.filter(type=lgc_models.INVOICE,
                                                     state=lgc_models.INVOICE_STATE_TOBEDONE)
        res['ready_invoices'] = invoices[:10]
        res['nb_items'] += len(invoices)
        quotations = lgc_models.Invoice.objects.filter(type=lgc_models.QUOTATION, state=lgc_models.INVOICE_STATE_PENDING)
        res['ready_quotations'] = quotations[:10]
        res['nb_items'] += len(quotations)

    return res

@register.simple_tag
def get_expiration_mapping(val):
    l = lgc_models.PERSON_EXPIRATIONS_CHOICES_COMPACT
    for i in l:
        if val == i[0]:
            return i[1]
    return val

@register.simple_tag
def get_process_progress(request):
    res = []
    res_cached = session_cache_get(request.session, 'process_progress')

    if res_cached:
        return res_cached

    person_processes = lgc_models.PersonProcess.objects.select_related('person').filter(active=True, person__responsible=request.user)[:10]

    for person_process in person_processes:
        stages_cnt = person_process.process.stages.count()
        if stages_cnt == 0:
            continue
        person_process_stages_cnt = lgc_models.PersonProcessStage.objects.filter(is_specific=False, person_process=person_process).count()
        progress = int((person_process_stages_cnt / stages_cnt) * 100)

        if person_process.person.host_entity:
            host_entity = ' (' + person_process.person.host_entity + ')'
        else:
            host_entity = ''

        if progress < 50:
            bg = 'bg-info'
        elif progress >= 50 and progress < 80:
            bg = 'bg-warning'
        else:
            bg = 'bg-danger'
        url = reverse_lazy('lgc-file', kwargs={'pk':person_process.person.id})
        res.append((person_process.person.first_name,
                    person_process.person.last_name, host_entity,
                    progress, bg, str(url)))

    session_cache_add(request.session, 'process_progress', res, 60)
    return res

@register.simple_tag
def get_pending_moderations(request):
    objs = employee_models.Employee.objects.select_related('user').filter(updated=True, user__person_user_set__responsible=request.user)

    res = {
        'objs': objs[:10],
        'nb_items': len(objs),
    }
    return res


def normalize_value(obj, key, val):
    if val == None or (val == False and type(val).__name__ == 'bool'):
        return ''

    if type(val).__name__ == 'bool' and val == True:
        return '<i class="fa fa-fw fa-check lgc-sorting-muted">'
    if type(val).__name__ == 'datetime':
        return date(val) + ' ' + time(val, 'H:i:s')

    """Get display value from choice fields."""
    display_attr = 'get_' + key + '_display'
    if hasattr(obj, display_attr):
        return getattr(obj, display_attr)()

    return val

@register.simple_tag
def get_table_th(label, value, order_by, order_params, exclude_list=None):
    label = str(label)
    res = '<th scope="col" class="lgc_no-wrap">' + label

    if exclude_list == None or value not in exclude_list:
        if order_by == value:
            res += '<a href="?' + order_params + '&order_by=-' + value + '"><i class="fa fa-fw fa-sort-up"></i></a>'
        elif order_by == '-' + value:
            res += '<a href="?' + order_params + '&order_by=' + value + '"><i class="fa fa-fw fa-sort-down"></i></a>'
        else:
            res += '<a href="?' + order_params +'&order_by=' + value + '"><i class="fa fa-fw fa-sort lgc-sorting-muted"></i></a>'
    res += '</th>'
    return mark_safe(res)

@register.simple_tag
def generate_table(header_values, object_list, order_by, order_params, url,
                   exclude_order_by_list=None):
    res = '<table class="table table-striped table-bordered table-hover">'
    res += '<thead>'
    res += '<tr>'
    for th in header_values:
        res += get_table_th(th[1], th[0], order_by, order_params,
                            exclude_order_by_list)
    res += '</tr>'

    res += '</thead>'
    res += '<tbody>'

    for obj in object_list:
        res += '<tr '
        if url:
            res += 'data-href="' + str(reverse_lazy(url, kwargs={'pk':obj.id})) + '"'
        res += 'class="clickable-row">'
        for th in header_values:
            try:
                extra_field = th[2]
                extra_field_label = th[3]
            except:
                extra_field = None

            if hasattr(obj, th[0]):
                val = normalize_value(obj, th[0], getattr(obj, th[0]))
                if type(val).__name__ == 'int':
                    res += '<td class="lgc_pull-right lgc_no-wrap">' + str(val)
                elif type(val).__name__ == 'float':
                    res += '<td class="lgc_pull-right lgc_no-wrap">' + str("%.2f"%val)
                else:
                    res += '<td class="lgc_no-wrap">' + str(val)

                if extra_field and extra_field in object_list[0].__dict__.keys():
                    val = getattr(obj, extra_field)
                    res += ' '
                    if type(val).__name__ == 'bool':
                        if val == True:
                            res += extra_field_label
                    else:
                        res += str(val)
                res += '</td>'
        res += '</tr>'

    res += '</tbody>'
    res += '</table>'
    return mark_safe(res)

@register.simple_tag
def is_local_user(user):
    return user.role in user_models.get_internal_roles()

@register.simple_tag
def is_external_user(user):
    return user.role in user_models.get_external_roles()

@register.filter
def getdefattr (obj, args):
    """ Try to get an attribute from an object.

    Example: {% if block|getattr:"editable,True" %}

    Beware that the default is always a string, if you want this
    to return False, pass an empty second argument:
    {% if block|getattr:"editable," %}
    """
    (attribute, default) = args.split(',')
    try:
        return obj.__getattribute__(attribute)
    except AttributeError:
         return  obj.__dict__.get(attribute, default)
    except:
        return default

@register.filter
def getattr(obj, arg):
    """ Try to get an attribute from an object.

    Example: {% if block|getattr:"editable,True" %}

    Beware that the default is always a string, if you want this
    to return False, pass an empty second argument:
    {% if block|getattr:'editable' %}
    """

    try:
        return obj.__getattribute__(arg)
    except:
        return ''

@register.filter
def tpl_hasattr(obj, arg):
    return hasattr(obj, arg)

@register.filter(is_safe=False)
def addf(value, arg):
    """Adds the arg to the value."""
    return round(float(value) + float(arg), 2)

@register.filter(is_safe=True)
def lgc_truncatewords(value, arg):
    """
    Truncate a string after `arg` number of words.
    Remove newlines within the string.
    """
    try:
        length = int(arg)
    except ValueError:  # Invalid literal for int().
        return value  # Fail silently.
    return Truncator(value).words(length, html=True, truncate='')

@register.simple_tag
def expiration_get_user_url(user, person):
    if user.role == user_models.ROLE_EMPLOYEE:
        return reverse_lazy('employee-file') + '?tab=lgc-tab-documents'
    if user.role in user_models.get_hr_roles():
        return reverse_lazy('hr-employee-file', kwargs={'pk':person.user.employee_user_set.id})
    return reverse_lazy('lgc-file', kwargs={'pk': person.id})
