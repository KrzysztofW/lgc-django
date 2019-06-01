from django.utils.formats import get_format
from datetime import datetime
from django.utils.translation import ugettext as _
from django.urls import reverse_lazy
import time
import os
import json
from django.conf import settings
from django.core.serializers import serialize
from django.core.mail import send_mail
from functools import wraps
from users.models import INTERNAL_ROLE_CHOICES
from string import Template
from common import lgc_types
from pathlib import Path

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

def pagination(request, context, url, default_order_by='id'):
    context['params'] = request.GET.urlencode()
    context['url'] = url
    order_by = request.GET.get('order_by', default_order_by)
    get_order = request.GET.copy()

    get_order.pop('order_by', '')
    context['order_params'] = get_order.urlencode()

    get_page = request.GET.copy()
    get_page.pop('page', '')
    context['page_params'] = get_page.urlencode()

    get_paginate = get_page.copy()
    get_paginate.pop('paginate', '')
    context['paginate_params'] = get_paginate.urlencode()

    context['order_by'] = order_by
    paginate = request.GET.get('paginate')
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
    if action == lgc_types.MsgType.NEW_EM:
        subject = _('new employee subject')
        tpl = 'message_employee'
    elif action == lgc_types.MsgType.NEW_HR:
        subject = _('new HR subject')
        tpl = 'message_employee'
    elif action == lgc_types.MsgType.DEL:
        subject = _('new account delete subject')
        tpl = 'message_delete'
    else:
        return

    lang = obj.language.lower()
    tpl_txt = tpl + '_' + lang + '.txt'
    tpl_html = tpl + '_' + lang + '.html'
    msg_tpl = read_template(tpl_txt)
    msg_tpl_html = read_template(tpl_html)

    name = obj.first_name + ' ' + obj.last_name
    url = reverse_lazy('user-token')[3:]
    url = settings.SITE_URL + '/' + lang + url + '?token=' + obj.token

    msg = msg_tpl.substitute(PERSON_NAME=name, URL=url)
    msg_html = msg_tpl_html.substitute(PERSON_NAME=name, URL=url)
    to = name + '<' + obj.email + '>'

    ret = send_mail(subject, msg, 'no-reply <no-reply@example.com>',
                    [to], html_message=msg_html)
    if ret != 1:
        raise RuntimeError('cannot send email')

    from datetime import datetime

def parse_date(date_str):
    """Parse date from string by DATE_INPUT_FORMATS of current language"""
    for item in get_format('DATE_INPUT_FORMATS'):
        try:
            return datetime.strptime(date_str, item).date()
        except (ValueError, TypeError):
            continue

    return None

def set_bold_search_attrs(objs, attrs, term, term_int=None):
    new_attrs = []

    for obj in objs:
        for attr in attrs:
            try:
                val = getattr(obj, attr)
            except:
                continue
            if type(val).__name__ == 'str':
                val = val.lower()
            try:
                if val.startswith(term):
                    bold_attr = 'b_' + attr
                    setattr(obj, bold_attr, val)
            except:
                if term_int and val == term_int:
                    bold_attr = 'b_' + attr
                    setattr(obj, bold_attr, val)
    for attr in attrs:
        new_attrs.append('b_' + attr)
    return new_attrs

def get_template(path, name):
    try:
        with Path(path, 'templates', name).open() as fh:
            return fh.read()
    except FileNotFoundError:
        raise Http404
