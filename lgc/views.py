from django.shortcuts import render

def home(request):
    return render(request, 'lgc/index.html', {'title':'Home'})

def login(request):
    return render(request, 'lgc/login.html', {'titile':'Login'})

def tables(request):
    return render(request, 'lgc/tables.html', {'title':'Tables'})

