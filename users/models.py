from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _
import common.validators as validators

EN = 'EN'
FR = 'FR'
LANGUAGE_CHOICES = (
    (EN, _('English')),
    (FR, _('French')),
)

ROLE_NONE      = ''
ROLE_JURIST    = 'JU'
ROLE_CONSULTANT = 'CO'
ROLE_HR_ADMIN   = 'HA'
ROLE_HR         = 'HR'
ROLE_EMPLOYEE   = 'EM'

EXTERNAL_ROLE_CHOICES = (
    (ROLE_HR_ADMIN,   _('HR Admin')),
    (ROLE_HR,         _('HR')),
    (ROLE_EMPLOYEE,   _('Employee')),
)

INTERNAL_ROLE_CHOICES = (
    (ROLE_NONE,         '------'),
    (ROLE_JURIST,     _('Jurist')),
    (ROLE_CONSULTANT, _('Consultant')),
)

ALL_ROLE_CHOICES = INTERNAL_ROLE_CHOICES + EXTERNAL_ROLE_CHOICES

def get_internal_roles():
    return [ROLE_NONE, ROLE_JURIST, ROLE_CONSULTANT]

def get_external_roles():
    return [ROLE_HR_ADMIN, ROLE_HR, ROLE_EMPLOYEE]

def get_hr_roles():
    return [ROLE_HR, ROLE_HR_ADMIN]

def get_jurist_queryset():
    return User.objects.filter(role__exact=ROLE_JURIST)

def get_consultant_queryset():
    return User.objects.filter(role__exact=ROLE_CONSULTANT)

def get_local_user_queryset():
    return get_jurist_queryset()|get_consultant_queryset()

def get_active_local_user_queryset():
    return (get_jurist_queryset()|get_consultant_queryset()).exclude(is_active=False)

def get_all_local_user_queryset():
    return get_jurist_queryset()|get_consultant_queryset()|User.objects.filter(role__exact=ROLE_NONE)

def get_employee_user_queryset():
    return User.objects.filter(role__exact=ROLE_EMPLOYEE)

def get_hr_user_queryset():
    return User.objects.filter(role__exact=ROLE_HR)|User.objects.filter(role__exact=ROLE_HR_ADMIN)

def get_external_user_queryset():
    return get_employee_user_queryset()|get_hr_user_queryset()

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

USER_STATUS_PENDING = 'P'
USER_STATUS_ACTIVE  = 'A'
USER_STATUS_DELETED_BY_EMPLOYEE = 'DE'
USER_STATUS_DELETED_BY_HR = 'DH'
USER_STATUS_CHOICES = (
    (USER_STATUS_PENDING, _('Pending')),
    (USER_STATUS_ACTIVE, _('Active')),
    (USER_STATUS_DELETED_BY_EMPLOYEE, _('Deleted by employee')),
    (USER_STATUS_DELETED_BY_HR, _('Deleted by HR')),
)

def get_user_deleted_statuses():
    return [ USER_STATUS_DELETED_BY_EMPLOYEE, USER_STATUS_DELETED_BY_HR ]

class User(AbstractUser):
    # changes email to unique and blank to false
    USERNAME_FIELD = 'email'
    email = models.EmailField(unique=True)

    # removes username from REQUIRED_FIELDS
    REQUIRED_FIELDS = []
    username = models.CharField(max_length=1, blank=True, null=True,
                                default=None)
    first_name = models.CharField(_('First name'), max_length=50, validators=[validators.alpha])
    last_name = models.CharField(_('Last name'), max_length=50, validators=[validators.alpha])

    role = models.CharField(max_length=2, choices=ALL_ROLE_CHOICES,
                            default=ROLE_JURIST, blank=True)
    billing = models.BooleanField(default=False)
    show_invoice_notifs = models.BooleanField(_('Show invoice notifications'),
                                              default=False)
    objects = UserManager()
    token = models.CharField(max_length=64, default="", blank=True)
    token_date = models.DateTimeField(null=True)
    password_last_update = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=2, choices=USER_STATUS_CHOICES,
                              default=USER_STATUS_PENDING)
    responsible = models.ManyToManyField("self", blank=True)
    hr_employees = models.ManyToManyField("self", blank=True,
                                          related_name='hr_employee_set')
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES,
                                default=EN)
    company = models.CharField(max_length=50, blank=True)

    def __str__(self):
        if self.first_name != '' or self.last_name != '':
            return self.first_name + ' ' + self.last_name
        return self.email

class UserOldPasswords(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    password = models.CharField(max_length=50)
