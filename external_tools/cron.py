#!/usr/bin/python3

from datetime import datetime, timedelta
import pdb, sys, os
import django
sys.path.append("")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lgc_base.settings")
django.setup()
from lgc.models import Invoice, PersonProcess
from users import views as user_views
from common import lgc_types
from django.core.mail import send_mail
from django.utils import translation
from django.utils.translation import ugettext as _
from django.urls import reverse_lazy
from django.conf import settings

def send_alert(objs, alert_type, cc=None):
    for p in objs.all():
        user_views.notify_user(p.person, p, alert_type, cc)

seven_day_diff = (datetime.today() -
                  timedelta(days=settings.FIRST_REMAINDER_DELAY)).strftime("%Y-%m-%d")
fourteen_day_diff = (datetime.today() -
                     timedelta(days=settings.SECOND_REMAINDER_DELAY)).strftime("%Y-%m-%d")

for day_diff in seven_day_diff, fourteen_day_diff:
    if day_diff == fourteen_day_diff:
        cc = settings.REMAINDER_RESP
    else:
        cc = []

    processes = PersonProcess.objects.filter(no_billing=False,
                                             invoice_alert=True,
                                             invoice_set=None,
                                             modification_date__contains=day_diff)
    send_alert(processes, lgc_types.MsgType.PROC_ALERT, cc)

    invoices = Invoice.objects.filter(last_modified_date__contains=day_diff).exclude(state='V')
    send_alert(invoices, lgc_types.MsgType.INVOICE_ALERT, cc)
