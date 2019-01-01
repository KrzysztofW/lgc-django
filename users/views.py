from urllib.parse import urlencode
from django.http import Http404
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout_then_login
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from .models import Profile
from .forms import UserCreateForm, UserUpdateForm, ProfileCreateForm
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  DeleteView)

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'users/list.html'
    context_object_name = 'users'

    def get_ordering(self):
        return self.request.GET.get('order_by', '-date_joined')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_queryset(self):
        term = self.request.GET.get('term', '')
        order_by = self.request.GET.get('order_by', '-date_joined')
        return User.objects.filter(username__icontains=term).order_by(order_by)|User.objects.filter(email__icontains=term)|User.objects.filter(first_name__icontains=term)|User.objects.filter(last_name__icontains=term)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_by = self.request.GET.get('order_by', '-date_joined')

        context['params'] = urlencode(self.request.GET)
        get_order = self.request.GET.copy()
        if 'order_by' in get_order:
            get_order.pop('order_by')
        context['order_params'] = urlencode(get_order)

        get_page = self.request.GET.copy()
        if 'page' in get_page:
            del get_page['page']
        context['page_params'] = urlencode(get_page)

        get_paginate = get_page.copy()
        if 'paginate' in get_paginate:
            del get_paginate['paginate']
        context['paginate_params'] = urlencode(get_paginate)

        context['order_by'] = order_by
        paginate = self.request.GET.get('paginate')
        if paginate == "25":
            context['25_selected'] = "selected"
        elif paginate == "50":
            context['50_selected'] = "selected"
        elif paginate == "100":
            context['100_selected'] = "selected"
        else:
            context['10_selected'] = "selected"
        return context

class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/user.html"
    context_object_name = 'context'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['u_form'] = UserCreateForm()
        context['p_form'] = ProfileCreateForm()

        return context

class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'users/confirm_delete.html'
    success_url = reverse_lazy('lgc-users')
    success_message = _("User deleted successfully.")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

@login_required
def create(request):
    if request.method == 'POST':
        u_form = UserCreateForm(request.POST)
        p_form = ProfileCreateForm(request.POST)

        if u_form.is_valid() and p_form.is_valid():
            user = u_form.save()
            profile = p_form.save(commit=False)
            profile.user = user
            profile.save()
            username = u_form.cleaned_data.get('username')
            messages.success(request,
                             _('The account for %(username)s has been created') %
                             { 'username': username})
            return redirect('lgc-user-create')
        context = {
            'u_form': u_form,
            'p_form': p_form
        }
        return render(request, 'users/create.html', context)

    context = {
        'u_form': UserCreateForm(),
        'p_form': ProfileCreateForm()
    }
    return render(request, 'users/create.html', context)

@login_required
def update(request, user_id):
    user = User.objects.filter(id=user_id)

    if user.count() != 1:
        raise Http404
    try:
        user[0].profile
    except:
        profile_exists = False
    else:
        profile_exists = True

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=user[0])
        if profile_exists:
            p_form = ProfileCreateForm(request.POST, instance=user[0].profile)
        else:
            p_form = ProfileCreateForm(request.POST)

        if u_form.is_valid() and p_form.is_valid():
            user = u_form.save()
            profile = p_form.save(commit=False)
            profile.user = user
            profile.save()
            username = u_form.cleaned_data.get('username')
            messages.success(request,
                             _('The account for %(username)s has been updated') %
                             { 'username': username})
            return redirect('lgc-users')
        context = {
            'u_form': u_form,
            'p_form': p_form,
            'update': 1,
            'user_id': user_id,
        }
        return render(request, 'users/create.html', context)

    if profile_exists:
        p_form = ProfileCreateForm(instance=user[0].profile)
    else:
        p_form = ProfileCreateForm
    context = {
        'u_form': UserUpdateForm(instance=user[0]),
        'p_form': p_form,
        'update': 1,
        'user_id': user_id,
    }
    return render(request, 'users/create.html', context)

@login_required
def profile(request):
    return render(request, 'users/profile.html')

@login_required
def logout_then_login_with_msg(request):
    messages.success(request, _('You were successfully logged-out.'))
    return logout_then_login(request)

@login_required
def ajax_view(request):
    term = request.GET.get('term', '')
    users = User.objects.filter(username__icontains=term)
    users = User.objects.filter(username__icontains=term)|User.objects.filter(email__icontains=term)|User.objects.filter(first_name__icontains=term)|User.objects.filter(last_name__icontains=term)
    users = users[:10]

    for u in users:
        if term in u.username.lower():
            u.b_username = u.username.lower()
        elif term in u.email.lower():
            u.b_email = u.email.lower()
        elif term in u.first_name.lower():
            u.b_first_name = u.first_name.lower()
        elif term in u.last_name.lower():
            u.b_last_name = u.last_name.lower()
    context = {
        'users': users
    }
    return render(request, 'users/search.html', context)
