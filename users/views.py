from common.utils import pagination, lgc_send_email, must_be_staff
from common import lgc_types
from django.http import Http404, HttpResponseForbidden
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout_then_login, LoginView as authLoginView
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext as _
from django.utils import translation
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from . import forms as user_forms
from lgc import models as lgc_models
from employee import models as employee_models
from lgc import views as lgc_views
from django.views.generic import (ListView, DetailView, CreateView,
                                  UpdateView, DeleteView)
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from ipaddress import IPv4Address, IPv4Network
from django.contrib.auth.signals import (user_logged_in, user_logged_out,
                                         user_login_failed)
from django.dispatch import receiver
from . import models as user_models
import os, logging, json

log = logging.getLogger('user')
User = get_user_model()

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'lgc/sub_generic_list.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_ordering(self):
        return self.request.GET.get('order_by', '-date_joined')

    def get_paginate_by(self, queryset):
        return self.request.GET.get('paginate', '10')

    def get_queryset(self):
        users = user_models.get_all_local_user_queryset()
        term = self.request.GET.get('term', '')
        order_by = self.get_ordering()
        if term == '':
            return users.order_by(order_by)
        objs = (users.filter(email__istartswith=term)|
                users.filter(first_name__istartswith=term)|
                users.filter(last_name__istartswith=term))
        return objs.order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Users')
        context['create_url'] = reverse_lazy('user-create')
        context['item_url'] = 'user'
        context['ajax_search_url'] = reverse_lazy('user-local-user-search-ajax')
        context['search_url'] = reverse_lazy('user-list')
        context['header_values'] = [
            ('email', 'E-mail'), ('first_name', _('First Name')),
            ('last_name', _('Last Name')), ('is_active', _('Active')),
            ('role', _('Role')), ('billing', _('Billing')),
            ('is_staff', _('Staff'))
        ]

        return pagination(self.request, context, reverse_lazy('user-list'))

class UserCreateView(LoginRequiredMixin, SuccessMessageMixin, UserPassesTestMixin,
                     CreateView):
    model = User
    template_name = 'users/create.html'
    success_message = _('User successfully created.')
    success_url = reverse_lazy('user-create')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('New User')
        return context

    def get_form(self):
        return super().get_form(form_class=user_forms.UserCreateForm)

    def test_func(self):
        return self.request.user.is_staff

class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UserPassesTestMixin,
                     UpdateView):
    model = User
    template_name = 'users/create.html'
    success_message = _('User successfully updated.')

    def get_success_url(self):
        return reverse_lazy('user', kwargs={'pk':self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Update User')
        context['delete_url'] = reverse_lazy('user-delete',
                                             kwargs={'pk': self.object.id})
        context['pw_reset_url'] = reverse_lazy('user-pw-reset',
                                               kwargs={'user_id': self.object.id})
        return context

    def get_form(self):
        return super().get_form(form_class=user_forms.UserUpdateForm)

    def test_func(self):
        return self.request.user.is_staff

def notify_user(user, obj, msg_type, cc=None):
    for u in user.responsible.all():
        try:
            lgc_send_email(obj, msg_type, u, cc)
        except Exception as e:
            log.error(e)

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'users/confirm_delete.html'
    success_url = reverse_lazy('user-list')
    title = _('Delete User')
    success_message = _('User successfully deleted.')
    profile_update = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        if not self.profile_update:
            cancel_url = reverse_lazy('user', kwargs={'pk': self.object.id})
            confirm_message = _('Are you sure you want to delete the account of %(firstname)s %(lastname)s')%{
                'firstname':self.object.first_name, 'lastname':self.object.last_name
            }
        else:
            cancel_url = reverse_lazy('user-profile')
            confirm_message = _('Are you sure you want to delete your account?')
        context['cancel_url'] = cancel_url
        context['profile_update'] = self.profile_update
        context['confirm_message'] = confirm_message
        return context

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        if not self.profile_update:
            return super().delete(request, *args, **kwargs)
        obj = self.get_object()
        obj.is_active = False
        obj.status = user_models.USER_STATUS_DELETED_BY_EMPLOYEE
        obj.save()
        notify_user(obj, obj, lgc_types.MsgType.DEL_REQ)

        return redirect('user-logout')

@login_required
@must_be_staff
def password_reset(request, user_id):
    user = User.objects.filter(id=user_id)
    title = _("Password Reset")
    form = user_forms.UserPasswordUpdateForm()

    if user.count() != 1:
        raise Http404
    if request.method == 'POST':
        form = user_forms.UserPasswordUpdateForm(request.POST,
                                                 instance=user[0])
        if form.is_valid():
            form.save()
            messages.success(request,
                             _('The password for %(firstname)s %(lastname)s has been successfully updated')%{
                                 'firstname':user[0].first_name, 'lastname':user[0].last_name})
            return redirect('user', user_id)

    context = {
        'form': form,
        'user': user[0],
        'title': title,
        'cancel_url': reverse_lazy('user', kwargs={'pk': user_id})

    }
    return render(request, 'users/password_reset.html', context)

def return_true(obj):
    return True

@login_required
def profile_delete(request):
    user_delete_view = UserDeleteView
    user_delete_view.title = _('Delete My Account')
    user_delete_view.success_url = reverse_lazy('user-logout')
    user_delete_view.success_message = _('Your account has been successfully deleted.')
    user_delete_view.profile_update = True
    user_delete_view.test_func = return_true
    view = user_delete_view.as_view()
    return view(request, pk=request.user.id)

@login_required
def profile_password_reset(request):
    title = _('Password Reset')
    form = user_forms.UserPasswordUpdateForm()

    if request.method == 'POST':
        form = user_forms.UserPasswordUpdateForm(request.POST,
                                                 instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request,
                             _('Your password has been successfully updated'))
            return redirect('user-profile')

    context = {
        'form': form,
        'title': title,
        'cancel_url': reverse_lazy('user-profile'),
        'profile_update': 1,
    }
    return render(request, 'users/password_reset.html', context)

@login_required
def update_profile(request):
    context = {
        'profile_update': 1,
        'title': _("My Account Profile"),
        'delete_url': reverse_lazy('user-profile-delete'),
        'pw_reset_url': reverse_lazy('user-profile-pw-reset'),
    }

    if request.method == 'POST':
        form = user_forms.UserUpdateProfileForm(request.POST,
                                                instance=request.user)

        if form.is_valid():
            user = form.save()
            if user.language != 'EN' and user.language != 'FR':
                raise Http404

            translation.activate(user.language)
            request.session[translation.LANGUAGE_SESSION_KEY] = user.language
            messages.success(request,
                             _('Your account profile has been updated'))

            if hasattr(user, 'person_user_set'):
                user.person_user_set.first_name = user.first_name
                user.person_user_set.last_name = user.last_name
                user.person_user_set.email = user.email
                user.person_user_set.save()
            return redirect('user-profile')

        context['form'] = form
    else:
        context['form'] = user_forms.UserUpdateProfileForm(instance=request.user)

    return render(request, 'users/create.html', context)

class LoginView(authLoginView):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        url_next = self.request.GET.get('next')

        if not url_next:
            return context

        url_next = url_next[4:]
        urls = [ '', 'user/profile/', 'user/logout/' ]
        for lang in settings.LANGUAGES:
            if url_next in urls:
                return context

        return context

    def redirect_language(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('lgc-home')

    def form_valid(self, form):
        form = super().form_valid(form)
        ip = self.request.META.get('REMOTE_ADDR')
        ip = IPv4Address(ip)

        translation.activate(self.request.user.language)
        self.request.session[translation.LANGUAGE_SESSION_KEY] = self.request.user.language

        for subnet in settings.ALLOWED_SESSION_NOTIMEOUT_SUBNETS:
            if ip in IPv4Network(subnet):
                self.request.session['no_session_expiry'] = True
                break

        if self.request.user.role in user_models.get_internal_roles():
            return self.redirect_language()

        if (self.request.user.password_last_update == None or
            self.request.user.password_last_update + timedelta(days=settings.AUTH_PASSWORD_EXPIRY) < timezone.now().date()):
            messages.error(self.request, _('Your password has expired. Please choose a new one'))
            token = lgc_views.token_generator()
            self.request.user.token = token
            self.request.user.token_date = timezone.now()
            self.request.user.save()
            logout(self.request)
            response = redirect('user-token')
            response['Location'] += '?token=' + token
            return response
        return self.redirect_language()

    def form_invalid(self, form):
        email = form.cleaned_data.get('username')
        user = None

        if email:
            try:
                user = User.objects.get(email=email)
            except:
                pass

        if user:
            translation.activate(user.language)
            if not user.is_active:
                messages.error(self.request,
                               _('Your account is no longer active, please contact your Office consultant.'))
                return super().form_invalid(form)
        try:
            messages.error(self.request, form.errors.get('__all__')[0])
        except:
            pass

        return super().form_invalid(form)

@login_required
def logout_then_login_with_msg(request):
    messages.success(request, _('You were successfully logged-out.'))
    return logout_then_login(request)

def __ajax_view(request, users):
    term = request.GET.get('term', '')
    term = term.lower()
    users = users.filter(email__istartswith=term)|users.filter(first_name__istartswith=term)|users.filter(last_name__istartswith=term)
    users = users[:10]

    for u in users:
        if u.email.lower().startswith(term):
            u.b_email = u.email.lower()
        if u.first_name.lower().startswith(term):
            u.b_first_name = u.first_name.lower()
        if u.last_name.lower().startswith(term):
            u.b_last_name = u.last_name.lower()
    context = {
        'users': users
    }
    return render(request, 'users/search.html', context)

def reset_password(request):
    title = _('Reset your password')
    context = {
        'title': title,
    }

    if request.method != 'POST':
        return render(request, 'users/forgotten_password.html')

    username = request.POST.get('username')
    if not username:
        return render(request, 'users/forgotten_password.html')
    try:
        user = User.objects.get(email=username)
    except:
        messages.error(request, _("The email does not match any account."))
        return render(request, 'users/forgotten_password.html')

    if user.is_active == False:
        messages.error(request, _('This account is not active.'))
        return render(request, 'users/forgotten_password.html')
    try:
        user.token = lgc_views.token_generator(pw_rst=True)
        user.token_date = timezone.now()
        user.save()

        lgc_send_email(user, lgc_types.MsgType.PW_RST, None)
    except Exception as e:
        messages.error(request, _('Cannot send email to `%(email)s` (%(err)s)')%{
            'email':user.email,
            'err': str(e)
        })
        return render(request, 'users/forgotten_password.html')

    messages.success(request, _('We sent an email to %(email)s with a link to help verify it is you. The link is valid for %(expiry)s hours.')%{
        'email':username,
        'expiry':settings.AUTH_TOKEN_EXPIRY
    })

    return redirect('user-login')

def token_set_account(request, user, form=None):
    user.token = ''
    user.token_date = None
    user.status = user_models.USER_STATUS_ACTIVE
    user.password_last_update = timezone.now().date()
    user.terms_opts = json.dumps({
        'date':str(timezone.now().strftime("%Y-%m-%d %H:%M:%S")),
        'ip':request.META.get('REMOTE_ADDR'),
        'agent':request.headers['User-Agent']
    })

    """This saves the user's password in form.cleaned_data['password1']"""
    if form:
        form.save()
    else:
        user.save()
    if (user.role != user_models.ROLE_EMPLOYEE or
        hasattr(user, 'person_user_set')):
        return
    p = lgc_models.Person()
    p.first_name = user.first_name
    p.last_name = user.last_name
    p.email = user.email
    p.modified_by = user
    p.user = user
    p.save()
    p.responsible.set(user.responsible.all())

    e = employee_models.Employee()
    e.first_name = user.first_name
    e.last_name = user.last_name
    e.email = user.email
    e.user = user
    e.modified_by = user
    e.save()

def handle_auth_token_disabled_account(request, user):
    title = _("Welcome to LGC")
    tpl = 'users/token_disabled_account.html'
    context = {
        'title': title,
        'user': user,
    }

    if request.method == 'POST':
        if request.POST.get('terms') != '1':
            messages.error(request,
                           _('You must accept the terms and conditions.'))
            return render(request, tpl, context)

        token_set_account(request, user)
        return render(request, 'users/token_disabled_account_success.html', context)
    return render(request, tpl, context)

def handle_auth_token(request):
    title = _("Welcome to LGC")
    token = request.GET.get('token', '')
    context = {
        'title': title,
    }

    if token == '':
        return render(request, 'users/token_bad.html', context)

    try:
        user = User.objects.get(token=token)
    except:
        return render(request, 'users/token_bad.html', context)

    if user.token_date + timedelta(hours=settings.AUTH_TOKEN_EXPIRY) < timezone.now():
        return render(request, 'users/token_bad.html', context)

    """Check if the account is really active"""
    if not user.is_active:
        return handle_auth_token_disabled_account(request, user)

    context['user'] = user
    if request.method == 'POST':
        if user.password == '' or lgc_views.is_token_pw_rst(token):
            form = user_forms.UserPasswordUpdateForm(request.POST, instance=user)
        else:
            form = user_forms.UserForcePasswordUpdateForm(request.POST, instance=user)
        context['form'] = form
        terms = request.POST.get('terms', '')

        if not form.is_valid() or terms != '1':
            return render(request, 'users/token.html', context)

        if user.password != '' and not lgc_views.is_token_pw_rst(token):
            if not check_password(form.cleaned_data['current_password'], form.instance.password):
                messages.error(request, _('The current password does not match.'))
                return render(request, 'users/token.html', context)
            if form.cleaned_data['current_password'] == form.cleaned_data['password1']:
                messages.error(request,
                               _('The new password and the old one must be different.'))
                return render(request, 'users/token.html', context)

        token_set_account(request, form.instance, form)
        messages.success(request,
                         _('The password for %(firstname)s %(lastname)s has been successfully set')%{
                             'firstname':user.first_name, 'lastname':user.last_name})
        return redirect('user-login')
    else:
        if user.password == '' or lgc_views.is_token_pw_rst(token):
            form = user_forms.UserPasswordUpdateForm()
        else:
            form = user_forms.UserForcePasswordUpdateForm()
        context['form'] = form
    return render(request, 'users/token.html', context)

@login_required
@must_be_staff
def ajax_local_user_seach_view(request):
    users = user_models.get_all_local_user_queryset()
    return __ajax_view(request, users)

@login_required
def ajax_hr_user_seach_view(request):
    if (request.user.role not in user_models.get_hr_roles() +
        user_models.get_internal_roles()):
        return HttpResponseForbidden()
    users = user_models.get_hr_user_queryset()
    return __ajax_view(request, users)

@login_required
def ajax_employee_user_seach_view(request):
    if request.user.role not in user_models.get_internal_roles():
        return HttpResponseForbidden()
    users = user_models.get_employee_user_queryset()
    return __ajax_view(request, users)

@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    log.info('login user: {user} (id:{id}, email:{email}) from: {ip}'.format(
        user=user, id=user.id, email=user.email, ip=ip))

@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    log.info('logout user: {user} (id:{id}, email:{email}) from: {ip}'.format(
        user=user, id=user.id, email=user.email, ip=ip))

@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, request, **kwargs):
    try:
        ip = request.META.get('REMOTE_ADDR')
        log.warning('login failed for: {credentials} from: {ip}'.format(
            credentials=credentials, ip=ip
        ))
    except:
        pass

def debug_login(request):
    if (not settings.DEBUG or
        not hasattr(settings, 'ALLOW_DEBUG_LOGIN') or
        not settings.ALLOW_DEBUG_LOGIN):
        raise Http404

    context = {
        'form': AuthenticationForm(),
    }

    if request.method != 'POST':
        return render(request, 'users/debug_login.html', context)

    username = request.POST['username']
    password = request.POST['password']

    if password == settings.DEBUG_LOGIN_PASSWD:
        user = User.objects.filter(email=username)
        if user.count() == 1:
            user = user[0]
            login(request, user)
            return redirect('lgc-home')

    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        return redirect('lgc-home')

    return render(request, 'users/debug_login.html', context)
