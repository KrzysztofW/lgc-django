from urllib.parse import urlencode

def pagination(django_object, context):
    context['params'] = urlencode(django_object.request.GET)
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
