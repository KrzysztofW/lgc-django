from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='lgc-home'),

    path('hr-create/', views.HRCreateView.as_view(), name='lgc-hr-create'),
    path('hr/<int:pk>/', views.HRUpdateView.as_view(), name='lgc-hr'),
    path('hr-list/', views.HRListView.as_view(), name='lgc-hrs'),
    path('hr-account-list/', views.HRAccountListView.as_view(), name='lgc-hr-accounts'),
    path('hr-delete/<int:pk>', views.HRDeleteView.as_view(),
         name='lgc-hr-delete'),

    path('file-create/', views.PersonCreateView.as_view(),
         name='lgc-file-create'),
    path('file-list/', views.PersonListView.as_view(), name='lgc-files'),
    path('file-delete/<int:pk>', views.PersonDeleteView.as_view(),
         name='lgc-file-delete'),
    path('file/<int:pk>/', views.PersonUpdateView.as_view(), name='lgc-file'),

    path('account-create/', views.InitiateAccount.as_view(), name='lgc-account-create'),
    path('account-list/', views.PendingAccounts.as_view(), name='lgc-accounts'),
    path('account/<int:pk>/', views.UpdatePendingAccount.as_view(), name='lgc-account'),
    path('account-delete/<int:pk>', views.DeletePendingAccount.as_view(),
         name='lgc-account-delete'),

    path('insert-employee/', views.ajax_insert_employee_view,
         name='lgc-insert-employee'),
    path('process-create/', views.ProcessCreateView.as_view(),
         name='lgc-process-create'),
    path('process-list/', views.ProcessListView.as_view(), name='lgc-processes'),
    path('process-delete/<int:pk>', views.ProcessDeleteView.as_view(),
         name='lgc-process-delete'),
    path('process/<int:pk>/', views.ProcessUpdateView.as_view(),
         name='lgc-process'),
]
