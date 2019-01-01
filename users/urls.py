from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import UserListView, UserDeleteView

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'),
         name='lgc-login'),
    path('logout/', views.logout_then_login_with_msg, name='lgc-logout'),
    path('create/', views.create, name='lgc-user-create'),
    path('list/', UserListView.as_view(), name='lgc-users'),
    path('delete/<int:pk>/', UserDeleteView.as_view(), name='lgc-user-delete'),
    path('search/ajax/', views.ajax_view, name='lgc-user-search-ajax'),
    path('<int:user_id>/', views.update, name='lgc-user'),
]
