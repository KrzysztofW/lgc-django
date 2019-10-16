from django.urls import path
from . import views
from lgc import views as lgc_views

urlpatterns = [
    path('expirations/', views.hr_expirations, name='hr-expirations'),
    path('employees/', views.HRPersonListView.as_view(), name='hr-employees'),
    path('file/<int:pk>', views.PersonUpdateView.as_view(), name='hr-employee-file'),
    path('initiate-case/', views.initiate_case, name='hr-initiate-case'),
    path('download/<int:pk>/', lgc_views.download_file, name='hr-download-file'),
]
