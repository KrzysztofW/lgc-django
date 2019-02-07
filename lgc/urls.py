from django.urls import path
from . import views
from .views import (
    PersonCreateView, PersonListView, PersonDeleteView, PersonUpdateView,
    ProcessCreateView, ProcessListView, ProcessDeleteView, ProcessUpdateView,
    InitiateCase, PendingCases, UpdatePendingCase, DeletePendingCase,
)

urlpatterns = [
    path('', views.home, name='lgc-home'),

    #path('hr-create/', HRCreateView.as_view(), name='lgc-hr-create'),
    #path('hr/<int:pk>/', HRUpdateView.as_view(), name='lgc-hr-update'),
    #path('hr-list/', HRListView.as_view(), name='lgc-hr-list'),
    #path('hr-delete/<int:pk>', HRDeleteView.as_view(), name='lgc-hr-delete'),


    path('file-create/', PersonCreateView.as_view(), name='lgc-file-create'),
    path('file-list/', PersonListView.as_view(), name='lgc-files'),
    path('file-delete/<int:pk>', PersonDeleteView.as_view(), name='lgc-file-delete'),
    path('file/<int:pk>/', PersonUpdateView.as_view(), name='lgc-file'),

    path('case-create/', InitiateCase.as_view(), name='lgc-case-create'),
    path('case-list/', PendingCases.as_view(), name='lgc-cases'),
    path('case/<int:pk>/', UpdatePendingCase.as_view(), name='lgc-case'),
    path('case-delete/<int:pk>', DeletePendingCase.as_view(), name='lgc-case-delete'),

    path('process-create/', ProcessCreateView.as_view(), name='lgc-process-create'),
    path('process-list/', ProcessListView.as_view(), name='lgc-processes'),
    path('process-delete/<int:pk>', ProcessDeleteView.as_view(), name='lgc-process-delete'),
    path('process/<int:pk>/', ProcessUpdateView.as_view(), name='lgc-process'),
]
