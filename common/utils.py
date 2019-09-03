from django.utils.formats import get_format
from datetime import datetime
from django.utils import translation
from django.utils.translation import ugettext as _
from django.urls import reverse_lazy
import time
import os
import json
from django.conf import settings
from django.core.serializers import serialize
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import Http404
from functools import wraps
from users.models import INTERNAL_ROLE_CHOICES
from string import Template as string_template
from django.template import Context, Template
from common import lgc_types
from pathlib import Path

MSG_TPL_DIR = 'msg_tpls'
CURRENT_DIR = Path(__file__).parent
ms_email_domains = ['hotmail', 'outlook', 'live', 'msg', 'passport']

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

def lgc_send_email(obj, action, from_user):
    prev_lang = translation.get_language()
    if action == lgc_types.MsgType.MODERATION:
        lang = from_user.language.lower()
        translation.activate(lang)

        subject = _("Moderation required")
        msg = _("""
Hi,\n
The file %(url)s has been modified by %(firstname)s %(lastname)s.
Your attention is required. Follow this link to moderate it: %(murl)s\n
Best Regards.
        """)%{'url':settings.SITE_URL + '/file/' + str(obj.user.person_user_set.id),
              'firstname':obj.modified_by.first_name,
              'lastname':obj.modified_by.last_name,
              'murl': settings.SITE_URL + '/emp/moderation/' + str(obj.id)}

        name = from_user.first_name + ' ' + from_user.last_name
        to = name + ' <' + from_user.email + '>'
        ret = send_mail(subject, msg, 'Office <no-reply@example.com>',
                        [to])
        translation.activate(prev_lang)
        if ret != 1:
            raise RuntimeError('cannot send email')
        return

    name = obj.first_name + ' ' + obj.last_name
    to = name + '<' + obj.email + '>'

    lang = obj.language.lower()
    translation.activate(lang)

    token_url = reverse_lazy('user-token')[3:]
    token_url = settings.SITE_URL + '/' + lang + token_url + '?token=' + obj.token

    if action == lgc_types.MsgType.NEW_EM:
        subject = _('Creation of your LGC account')
        tpl = 'message_employee'
    elif action == lgc_types.MsgType.NEW_HR:
        subject = _('Creation of your LGC account')
        tpl = 'message_hr'
    elif action == lgc_types.MsgType.DEL:
        subject = _('Confirmation - your “my KWA” account has been deleted')
        tpl = 'message_user_deletion'
    elif action == lgc_types.MsgType.PW_RST:
        subject = _("Confirm it's you to access your LGC account")
        msg = _("""
        Hi %(firstname)s %(lastname)s,\n

        It looks like you're having trouble signing into your account.\n

        Please follow this link: %(token)s
        to verify your identity and access your account. (It's only good for %(expiry)d hours.)\n

        If you don't recognize this activity, please contact us (contact@example.com)
        """)%{'firstname':obj.first_name,
              'lastname':obj.last_name,
              'token': token_url,
              'expiry':settings.AUTH_TOKEN_EXPIRY}
        ret = send_mail(subject, msg, 'Office <no-reply@example.com>',
                        [to])

        translation.activate(prev_lang)
        if ret != 1:
            raise RuntimeError('cannot send email')
        return
    else:
        translation.activate(prev_lang)
        return

    email_hostname = obj.email.split("@", 1)[1]
    email_hostname = email_hostname.split(".", 1)[0]

    if email_hostname in ms_email_domains:
        logo_url = settings.SITE_URL + '/static/lgc/images/mail_logo.png'
    else:
        logo_url = get_template(CURRENT_DIR, 'common/' + 'logo_inline_image.txt')

    tpl_txt = tpl + '.txt'
    tpl_html = tpl + '.html'
    msg_tpl = Template(get_template(CURRENT_DIR, 'common/' + tpl_txt)).render(Context())
    msg_tpl_html = Template(get_template(CURRENT_DIR, 'common/' + tpl_html)).render(Context())

    msg_tpl = string_template(msg_tpl)
    msg_tpl_html = string_template(msg_tpl_html)

    from_name = from_user.first_name + ' ' + from_user.last_name
    msg = msg_tpl.substitute(PERSON_NAME=name, URL=settings.SITE_URL,
                             TOKEN_URL=token_url, PERSON_IN_CHARGE=from_name,
                             LOGO_URL=logo_url)
    msg_html = msg_tpl_html.substitute(PERSON_NAME=name, URL=settings.SITE_URL,
                                       TOKEN_URL=token_url,
                                       PERSON_IN_CHARGE=from_name,
                                       LOGO_URL=logo_url)

    ret = send_mail(subject, msg, from_name + ' <' + from_user.email + '>',
                    [to], html_message=msg_html)

    translation.activate(prev_lang)
    if ret != 1:
        raise RuntimeError('cannot send email')

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
