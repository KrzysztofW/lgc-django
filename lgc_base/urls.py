"""lgc_base URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from lgc import views as lgc_views
from users import views as users_views
from users.views import (UserListView, UserDetailView, UserUpdateView,
                         UserDeleteView)

urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns += i18n_patterns(
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'),
         name='lgc-login'),
    path('logout/', users_views.logout_then_login_with_msg, name='lgc-logout'),
    path('', include('lgc.urls')),
    path('file/', lgc_views.file, name='lgc-file'),
    path('user-create/', users_views.create, name='lgc-user-create'),
    path('users/', UserListView.as_view(), name='lgc-users'),
    path('users/search/ajax/', users_views.ajax_view, name='lgc-user-search-ajax'),
)
