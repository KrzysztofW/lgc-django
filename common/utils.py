import time
import os
import json
from django.conf import settings
from django.core.serializers import serialize
from django.core.mail import send_mail
from urllib.parse import urlencode
from functools import wraps
from users.models import INTERNAL_ROLE_CHOICES
from string import Template

MSG_TPL_DIR = 'msg_tpls'

def must_be_staff(view_func):
    @wraps(view_func)
    def func_wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        if not request.user.role not in INTERNAL_ROLE_CHOICES:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return func_wrapper

def pagination(django_object, context, url):
    context['params'] = urlencode(django_object.request.GET)
    context['url'] = url
    order_by = django_object.request.GET.get('order_by', 'id')
    get_order = django_object.request.GET.copy()

    if 'order_by' in get_order:
        get_order.pop('order_by')
        context['order_params'] = urlencode(get_order)

    get_page = django_object.request.GET.copy()
    if 'page' in get_page:
        del get_page['page']
    context['page_params'] = urlencode(get_page)

    get_paginate = get_page.copy()
    if 'paginate' in get_paginate:
        del get_paginate['paginate']
    context['paginate_params'] = urlencode(get_paginate)

    context['order_by'] = order_by
    paginate = django_object.request.GET.get('paginate')
    if paginate == "25":
        context['25_selected'] = "selected"
    elif paginate == "50":
        context['50_selected'] = "selected"
    elif paginate == "100":
        context['100_selected'] = "selected"
    else:
        context['10_selected'] = "selected"

    return context

def queue_object_request(obj):
    if obj == None:
        return
    s = serialize('json', [obj])
    filename = os.path.join(settings.LGC_QUEUE_PATH, str(obj.id))
    with open(filename, "w") as f:
        f.write(s)

def queue_request(req_type, action, id, form, relations = None):
    resp = []
    rel = []

    if form == None:
        return

    for u in form['responsible']:
        resp.append(u.email)

    if relations != None:
        for r in relations:
            if r.email:
                rel.append(r.email)

    s = json.dumps([req_type, action, {
        'first_name':form['first_name'],
        'last_name':form['last_name'],
        'email':form['email'],
        'company':form['company'],
        'lang':form['language'],
        'new_token': form['new_token'],
        "responsible":resp,
        "relations":rel
    }])
    filename = os.path.join(settings.LGC_QUEUE_PATH, str(id))
    with open(filename, "w") as f:
        f.write(s + "\n")

def read_template(filename):
    path = os.path.join('common', MSG_TPL_DIR, filename)
    with open(path, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

def lgc_send_email(obj, action):
    msg_tpl = read_template('message_employee_en.txt')
    msg_tpl_html = read_template('message_employee_en.html')
    msg = msg_tpl.substitute(PERSON_NAME=obj.first_name + ' ' + obj.last_name,
                             URL='')
    msg_html = msg_tpl_html.substitute(PERSON_NAME=obj.first_name + ' ' +
                                       obj.last_name, URL='')

    subject = 'test subject'
    to = obj.first_name + ' ' + obj.last_name + '<' + obj.email + '>'

    # XXX don't send emails for now
    return
    ret = send_mail(subject, msg, 'no-reply <no-reply@example.com>',
                    [to], html_message=msg_html)
    if ret != 1:
        raise RuntimeError('cannot send email')
