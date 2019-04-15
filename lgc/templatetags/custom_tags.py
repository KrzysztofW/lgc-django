from django import template
from users import models as user_models
from lgc import models as lgc_models
from lgc import views as lgc_views
from django.conf import settings
from django.utils import timezone
from django.urls import reverse_lazy
import datetime

register = template.Library()

@register.simple_tag
def get_notification_menu(request):
    res = {}
    expirations = lgc_models.Expiration.objects.filter(person__responsible=request.user).filter(enabled=True).order_by('end_date')
    compare_date = timezone.now().date() + datetime.timedelta(days=settings.EXPIRATIONS_NB_DAYS)
    expirations = expirations.filter(end_date__lte=compare_date)
    res['expirations'] = expirations[:10]
    res['nb_items'] = len(expirations)
    res['today'] = timezone.now().date()
    return res

@register.simple_tag
def get_expiration_mapping(val):
    l = lgc_models.PERSON_SPOUSE_EXPIRATIONS_CHOICES_COMPACT
    for i in l:
        if val == i[0]:
            return i[1]
    return val

@register.simple_tag
def get_process_progress(request):
    res = []
    external_users = user_models.get_employee_user_queryset()|user_models.get_hr_user_queryset()
    files = lgc_models.Person.objects.filter(responsible=request.user)
    files = lgc_models.Person.objects.filter(modified_by__in=external_users).order_by('modification_date')

    person_common_view = lgc_views.PersonCommonView()

    for f in files:
        person_common_view.object = f
        person_process = person_common_view.get_active_person_process()
        if person_process == None:
            continue
        stages = person_common_view.get_process_stages(person_process.process)
        if stages == None or stages.count() == 0:
            return
        person_process_stages = person_common_view.get_person_process_stages(person_process)
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
