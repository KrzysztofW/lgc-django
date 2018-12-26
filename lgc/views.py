from django.shortcuts import render

def home(request):
    return render(request, 'lgc/index.html', {'title':'Home'})

