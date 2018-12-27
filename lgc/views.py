from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _

@login_required
def home(request):
    return render(request, 'lgc/index.html', {'title':'Home'})

@login_required
def tables(request):
    return render(request, 'lgc/tables.html', {'title':'Tables'})

@login_required
def file(request):
    title = _("New File")
    return render(request, 'lgc/file.html', {'title':title})
