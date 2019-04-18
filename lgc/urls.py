from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='lgc-home'),

    path('hr-create/', views.HRCreateView.as_view(), name='lgc-hr-create'),
    path('hr/<int:pk>/', views.HRUpdateView.as_view(), name='lgc-hr'),
    path('hr-account-list/', views.HRAccountListView.as_view(), name='lgc-hr-accounts'),
    path('hr-delete/<int:pk>', views.HRDeleteView.as_view(),
         name='lgc-hr-delete'),

    path('file-create/', views.PersonCreateView.as_view(),
         name='lgc-file-create'),
    path('file-list/', views.PersonListView.as_view(), name='lgc-files'),
    path('file-delete/<int:pk>', views.PersonDeleteView.as_view(),
         name='lgc-file-delete'),
    path('file/<int:pk>/', views.PersonUpdateView.as_view(), name='lgc-file'),
    path('file-search/ajax/', views.ajax_file_search_view,
         name='lgc-file-search-ajax'),

    path('account-create/', views.InitiateAccount.as_view(), name='lgc-account-create'),
    path('account-list/', views.Accounts.as_view(), name='lgc-accounts'),
    path('account/<int:pk>/', views.UpdateAccount.as_view(), name='lgc-account'),
    path('account-link/<int:pk>/', views.InitiateAccount.as_view(),
         name='lgc-account-link'),
    path('account-delete/<int:pk>', views.DeleteAccount.as_view(),
         name='lgc-account-delete'),

    path('insert-employee/', views.ajax_insert_employee_view,
         name='lgc-insert-employee'),
    path('process-create/', views.ProcessCreateView.as_view(),
         name='lgc-process-create'),
    path('process-list/', views.ProcessListView.as_view(),
         name='lgc-processes'),
    path('process-delete/<int:pk>', views.ProcessDeleteView.as_view(),
         name='lgc-process-delete'),
    path('process/<int:pk>/', views.ProcessUpdateView.as_view(),
         name='lgc-process'),
    path('process-search/ajax/', views.ajax_process_search_view,
         name='lgc-process-search-ajax'),

    path('process-stage-create/', views.ProcessStageCreateView.as_view(),
         name='lgc-process-stage-create'),
    path('process-stage-list/', views.ProcessStageListView.as_view(),
         name='lgc-process-stages'),
    path('process-stage-delete/<int:pk>',
         views.ProcessStageDeleteView.as_view(),
         name='lgc-process-stage-delete'),
    path('process-stage/<int:pk>/', views.ProcessStageUpdateView.as_view(),
         name='lgc-process-stage'),
    path('process-stage-search/ajax/', views.ajax_process_stage_search_view,
         name='lgc-process-stage-search-ajax'),

    path('person-process-list/<int:pk>/', views.PersonProcessListView.as_view(),
         name='lgc-person-processes'),
    path('person-process/<int:pk>/', views.PersonProcessUpdateView.as_view(),
         name='lgc-person-process'),
    path('person-process-search/ajax/<int:pk>', views.ajax_person_process_search_view,
         name='lgc-person-process-search-ajax'),

    path('download/<int:pk>/', views.download_file, name='lgc-download-file'),

    path('expirations/', views.expirations, name='lgc-expirations'),
]
