from django import template
from users import models as user_models
from lgc import models as lgc_models
from employee import models as employee_models
from lgc import views as lgc_views
from django.conf import settings
from django.utils import timezone
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from django.template.defaultfilters import date, time
import datetime

User = get_user_model()
register = template.Library()

@register.simple_tag
def get_notification_menu(request):
    res = {}
    expirations = lgc_models.Expiration.objects.filter(person__responsible=request.user).filter(enabled=True).order_by('end_date')
    compare_date = timezone.now().date() + datetime.timedelta(days=settings.EXPIRATIONS_NB_DAYS)
    expirations = expirations.filter(end_date__lte=compare_date)
    deletion_requests = User.objects.filter(status__in=user_models.get_user_deleted_statuses())
    res['expirations'] = expirations[:10]
    res['deletion_requests'] = deletion_requests[:5]
    res['nb_items'] = len(expirations) + len(deletion_requests)
    res['today'] = timezone.now().date()
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
    external_users = user_models.get_employee_user_queryset()|user_models.get_hr_user_queryset()
    files = lgc_models.Person.objects.filter(responsible=request.user)
    # files = files.filter(modified_by__in=external_users).order_by('modification_date')
    person_common_view = lgc_views.PersonCommonView()

    for f in files:
        person_common_view.object = f
        person_processes = person_common_view.get_active_person_processes()
        if person_processes == None:
            continue
        for person_process in person_processes:
            stages = person_process.process.stages.all()
            if stages.count() == 0:
                continue
            person_process_stages = lgc_models.PersonProcessStage.objects.filter(is_specific=False).filter(person_process=person_process)
            progress = (person_process_stages.count() / stages.count()) * 100

            if f.host_entity:
                host_entity = ' (' + f.host_entity + ')'
            else:
                host_entity = ''
            progress = int(progress)

            if progress < 50:
                bg = 'bg-info'
            elif progress >= 50 and progress < 80:
                bg = 'bg-warning'
            else:
                bg = 'bg-danger'
            url = reverse_lazy('lgc-file', kwargs={'pk':f.id})
            res.append((f.first_name, f.last_name, host_entity, int(progress),
                        bg, url))
            if len(res) > 10:
                return res
    return res

@register.simple_tag
def get_pending_moderations(request):
    objs = employee_models.Employee.objects.filter(updated=True)
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
def get_table_th(label, value, order_by, order_params):
    label = str(label)
    res = '<th scope="col" class="lgc_no-wrap">' + label

    if order_by == value:
        res += '<a href="?' + order_params + '&order_by=-' + value + '"><i class="fa fa-fw fa-sort-up"></i></a>'
    elif order_by == '-' + value:
        res += '<a href="?' + order_params + '&order_by=' + value + '"><i class="fa fa-fw fa-sort-down"></i></a>'
    else:
        res += '<a href="?' + order_params +'&order_by=' + value + '"><i class="fa fa-fw fa-sort lgc-sorting-muted"></i></a>'
    res += '</th>'
    return mark_safe(res)

@register.simple_tag
def generate_table(header_values, object_list, order_by, order_params, url):
    res = '<table class="table table-striped table-bordered table-hover">'
    res += '<thead>'
    res += '<tr>'
    for th in header_values:
        res += get_table_th(th[0], th[1], order_by, order_params)
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

            if hasattr(obj, th[1]):
                val = normalize_value(obj, th[1], getattr(obj, th[1]))
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
