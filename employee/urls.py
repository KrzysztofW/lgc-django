from django.urls import path
from . import views
from lgc import views as lgc_views

urlpatterns = [
    path('my-file/', views.my_file, name='employee-file'),
    path('my-expirations/', views.my_expirations, name='employee-expirations'),
    path('moderations/', views.moderations, name='employee-moderations'),
    path('moderation/<int:pk>/', views.moderation, name='employee-moderation'),
    path('download/<int:pk>/', lgc_views.download_file, name='employee-download-file'),
]
