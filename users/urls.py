from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import UserListView, UserDeleteView

urlpatterns = [
    path('login/', views.LoginView.as_view(template_name='users/login.html'),
         name='user-login'),
    path('reset-pw/', views.reset_password, name='user-reset-pw'),
    path('logout/', views.logout_then_login_with_msg, name='user-logout'),
    path('create/', views.UserCreateView.as_view(), name='user-create'),
    path('list/', UserListView.as_view(), name='user-list'),
    path('delete/<int:pk>/', UserDeleteView.as_view(), name='user-delete'),

    path('local-search/ajax/', views.ajax_local_user_seach_view,
         name='user-local-user-search-ajax'),
    path('hr-search/ajax/', views.ajax_hr_user_seach_view,
         name='user-hr-search-ajax'),
    path('employee-search/ajax/', views.ajax_employee_user_seach_view,
         name='user-employee-search-ajax'),

    path('<int:pk>/', views.UserUpdateView.as_view(), name='user'),
    path('pw-reset/<int:user_id>/', views.password_reset, name='user-pw-reset'),
    path('profile/', views.update_profile, name='user-profile'),
    path('profile-pw-reset/', views.profile_password_reset,
         name='user-profile-pw-reset'),
    path('delete-profile/', views.profile_delete, name='user-profile-delete'),

    path('auth/', views.handle_auth_token, name='user-token'),

    path('debug-login/', views.debug_login, name='user-debug-login'),
]
