import time
import os
import json
from django.conf import settings
from django.core.serializers import serialize
from urllib.parse import urlencode
from functools import wraps

def must_be_staff(view_func):
    @wraps(view_func)
    def func_wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
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
