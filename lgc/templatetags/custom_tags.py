from django import template
from users import models as user_models
from lgc import models as lgc_models

register = template.Library()

@register.simple_tag
def get_notification_menu(request):
    res = {}
    external_users = user_models.get_employee_user_queryset()|user_models.get_hr_user_queryset()
    files = lgc_models.Person.objects.filter(responsible=request.user).filter(modified_by__in=external_users)
    res['updated_files'] = files[:5]
    res['nb_items'] = len(files)
    return res
