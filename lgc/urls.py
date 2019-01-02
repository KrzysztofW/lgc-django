from django.urls import path
from . import views
from .views import (
    PersonCreateView, PersonListView, PersonDeleteView, PersonUpdateView
)

urlpatterns = [
    path('', views.home, name='lgc-home'),
    path('file-create/', PersonCreateView.as_view(), name='lgc-file-create'),
    path('file-list/', PersonListView.as_view(), name='lgc-files'),
    path('file-delete/<int:pk>', PersonDeleteView.as_view(), name='lgc-file-delete'),
    path('file/<int:pk>/', PersonUpdateView.as_view(), name='lgc-file'),
]
