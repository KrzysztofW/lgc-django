from django.urls import path
from . import views

urlpatterns = [
    # name is referenced in template .html files
    path('', views.home, name='home'),
]
