from django.urls import path
from . import views

urlpatterns = [
    path('my-file/', views.my_file, name='employee-file'),
    path('my-expirations/', views.my_expirations, name='employee-expirations'),
    path('moderations/', views.moderations, name='employee-moderations'),
    path('moderation/<int:pk>/', views.moderation, name='employee-moderation'),
]
