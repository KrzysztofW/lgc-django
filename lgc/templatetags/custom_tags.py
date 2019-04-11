from django import template
from users import models as user_models
from lgc import models as lgc_models
from django.conf import settings
from django.utils import timezone
import datetime

register = template.Library()

@register.simple_tag
def get_notification_menu(request):
    res = {}
    external_users = user_models.get_employee_user_queryset()|user_models.get_hr_user_queryset()
    files = lgc_models.Person.objects.filter(responsible=request.user).filter(modified_by__in=external_users)
    res['updated_files'] = files[:5]
    expirations = lgc_models.Expiration.objects.filter(person__responsible=request.user).filter(enabled=True).order_by('end_date')
    compare_date = timezone.now().date() + datetime.timedelta(days=settings.EXPIRATIONS_NB_DAYS)
    expirations = expirations.filter(end_date__lte=compare_date)
    res['expirations'] = expirations[:5]
    res['nb_items'] = len(files) + len(expirations)
    res['today'] = timezone.now().date()
    return res

@register.simple_tag
def get_expiration_mapping(val):
    l = lgc_models.PERSON_SPOUSE_EXPIRATIONS_CHOICES_COMPACT
    for i in l:
        if val == i[0]:
            return i[1]
    return val
