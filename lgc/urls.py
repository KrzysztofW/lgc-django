from django.urls import path
from . import views
from .views import (
    PersonCreateView, PersonListView, PersonDeleteView, PersonUpdateView,
    ProcessCreateView, ProcessListView, ProcessDeleteView, ProcessUpdateView
)

urlpatterns = [
    path('', views.home, name='lgc-home'),
    path('file-create/', PersonCreateView.as_view(), name='lgc-file-create'),
    path('file-list/', PersonListView.as_view(), name='lgc-files'),
    path('file-delete/<int:pk>', PersonDeleteView.as_view(), name='lgc-file-delete'),
    path('file/<int:pk>/', PersonUpdateView.as_view(), name='lgc-file'),

    path('process-create/', ProcessCreateView.as_view(), name='lgc-process-create'),
    path('process-list/', ProcessListView.as_view(), name='lgc-processes'),
    path('process-delete/<int:pk>', ProcessDeleteView.as_view(), name='lgc-process-delete'),
    path('process/<int:pk>/', ProcessUpdateView.as_view(), name='lgc-process'),

]
