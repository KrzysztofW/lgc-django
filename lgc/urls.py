from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='lgc-home'),

    path('hr-create/', views.HRCreateView.as_view(), name='lgc-hr-create'),
    path('hr/<int:pk>/', views.HRUpdateView.as_view(), name='lgc-hr'),
    path('hr-list/', views.HRListView.as_view(), name='lgc-hrs'),
    path('hr-case-list/', views.HRCaseListView.as_view(), name='lgc-hr-cases'),
    path('hr-delete/<int:pk>', views.HRDeleteView.as_view(),
         name='lgc-hr-delete'),

    path('file-create/', views.PersonCreateView.as_view(),
         name='lgc-file-create'),
    path('file-list/', views.PersonListView.as_view(), name='lgc-files'),
    path('file-delete/<int:pk>', views.PersonDeleteView.as_view(),
         name='lgc-file-delete'),
    path('file/<int:pk>/', views.PersonUpdateView.as_view(), name='lgc-file'),

    path('case-create/', views.InitiateCase.as_view(), name='lgc-case-create'),
    path('case-list/', views.PendingCases.as_view(), name='lgc-cases'),
    path('case/<int:pk>/', views.UpdatePendingCase.as_view(), name='lgc-case'),
    path('case-delete/<int:pk>', views.DeletePendingCase.as_view(),
         name='lgc-case-delete'),

    path('insert-file/', views.ajax_insert_file_view, name='lgc-insert-file'),
    path('process-create/', views.ProcessCreateView.as_view(),
         name='lgc-process-create'),
    path('process-list/', views.ProcessListView.as_view(), name='lgc-processes'),
    path('process-delete/<int:pk>', views.ProcessDeleteView.as_view(),
         name='lgc-process-delete'),
    path('process/<int:pk>/', views.ProcessUpdateView.as_view(),
         name='lgc-process'),
]
