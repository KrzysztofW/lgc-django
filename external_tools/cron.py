#!/usr/bin/python3

from datetime import datetime, timedelta
import pdb, sys, os, subprocess
import django
sys.path.append("")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lgc_base.settings")
django.setup()
from lgc import models as lgc_models
from users import views as user_views
from common import lgc_types
from django.core.mail import send_mail
from django.utils import translation
from django.utils.translation import ugettext as _
from django.urls import reverse_lazy
from django.conf import settings
from django import http
from django.core.mail.message import EmailMessage
from string import Template as string_template

seven_day_diff = (datetime.today() -
                  timedelta(days=settings.FIRST_REMINDER_DELAY)).strftime("%Y-%m-%d")
fourteen_day_diff = (datetime.today() -
                     timedelta(days=settings.SECOND_REMINDER_DELAY)).strftime("%Y-%m-%d")

def send_alert(objs, alert_type, cc=None):
    for p in objs.all():
        user_views.notify_user(p.person, p, alert_type, cc)

"""Process reminders"""
for day_diff in seven_day_diff, fourteen_day_diff:
    if day_diff == fourteen_day_diff:
        cc = settings.REMINDER_RESP
    else:
        cc = []

    processes = lgc_models.PersonProcess.objects.filter(no_billing=False,
                                                        invoice_alert=True,
                                                        invoice_set=None,
                                                        modification_date__contains=day_diff)
    send_alert(processes, lgc_types.MsgType.PROC_ALERT, cc)

    invoices = lgc_models.Invoice.objects.filter(last_modified_date__contains=day_diff,
                                                 state=lgc_models.INVOICE_STATE_TOBEDONE)
    send_alert(invoices, lgc_types.MsgType.INVOICE_ALERT, cc)


"""Billing reminders"""
for r in lgc_models.InvoiceReminder.objects.filter(enabled=True):
    day_diff = (datetime.today() -
                timedelta(days=r.number_of_days)).strftime("%Y-%m-%d")
    invoices = lgc_models.Invoice.objects.filter(last_modified_date__contains=day_diff,
                                                 state=lgc_models.INVOICE_STATE_DONE,
                                                 type=lgc_models.INVOICE)
    for i in invoices.all():
        response = http.HttpResponse(content_type='application/pdf')
        filename = 'FA' + str(i.number).zfill(5) + '.pdf'
        pdf = subprocess.Popen(os.path.join(settings.BASE_DIR, 'php_pdf/print.php') +
                               ' ' + str(i.id),
                               shell=True, stdout=subprocess.PIPE).stdout.read()
        email = EmailMessage()
        if i.language == 'FR':
            email.subject = r.subject_fr
            body = r.template_fr
        else:
            email.subject = r.subject_en
            body = r.template_en

        email.body = string_template(body).substitute(INVOICE_DATE=i.invoice_date,
                                                      FIRST_NAME=i.po_first_name,
                                                      LAST_NAME=i.po_last_name)
        email.from_email = settings.INVOICE_REMINDER_EMAIL
        email.to = [ i.po_email ]
        email.bcc = [ settings.INVOICE_REMINDER_EMAIL ]
        email.attach(filename=filename, mimetype='application/pdf', content=pdf)
        email.send()
