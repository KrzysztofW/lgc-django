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

    path('local-search/ajax/', views.ajax_local_user_seach_view,
         name='lgc-local-user-search-ajax'),
    path('hr-search/ajax/', views.ajax_hr_user_seach_view,
         name='lgc-hr-user-search-ajax'),
    path('employee-search/ajax/', views.ajax_employee_user_seach_view,
         name='lgc-employee-user-search-ajax'),

    path('<int:user_id>/', views.update, name='lgc-user'),
    path('pw-reset/<int:user_id>/', views.password_reset, name='lgc-pw-reset'),
    path('profile/', views.update_profile, name='lgc-profile'),
    path('profile-pw-reset/', views.profile_password_reset,
         name='lgc-profile-pw-reset'),

    path('auth/', views.handle_auth_token, name='lgc-token'),
]
