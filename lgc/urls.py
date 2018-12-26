from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='lgc-home'),
    path('tables/', views.tables, name='lgc-tables'),
    path('login/', views.login, name='lgc-login'),
]
