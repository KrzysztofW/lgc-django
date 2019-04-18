from django.urls import path
from . import views

urlpatterns = [
    path('expirations/', views.hr_expirations, name='hr-expirations'),
    path('employees/', views.HRPersonListView.as_view(), name='hr-employees'),
    path('initiate/', views.InitiateAccountByHR.as_view(),
         name='hr-initiate-account'),
    path('update/<int:pk>', views.UpdateAccountByHR.as_view(),
         name='hr-update-account'),
    path('delete/<int:pk>', views.HRDeleteAccountView.as_view(),
         name='hr-delete-account'),
]
