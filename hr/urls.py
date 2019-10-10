from django.urls import path
from . import views
from lgc import views as lgc_views

urlpatterns = [
    path('expirations/', views.hr_expirations, name='hr-expirations'),
    path('employees/', views.HRPersonListView.as_view(), name='hr-employees'),
    path('file/<int:pk>', views.PersonUpdateView.as_view(), name='hr-employee-file'),
    path('create/', views.CreateAccountByHR.as_view(),
         name='hr-create-account'),
    path('update/<int:pk>', views.UpdateAccountByHR.as_view(),
         name='hr-update-account'),
    path('delete/<int:pk>', views.HRDeleteAccountView.as_view(),
         name='hr-delete-account'),
    path('download/<int:pk>/', lgc_views.download_file, name='hr-download-file'),
]
