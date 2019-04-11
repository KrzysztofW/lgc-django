from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _

ENGLISH = 'EN'
FRENCH = 'FR'
LANGUAGE_CHOICES = (
    (ENGLISH, _('English')),
    (FRENCH, _('French')),
)

JURIST    = 'JU'
CONSULTANT = 'CO'
HR_ADMIN   = 'HA'
HR         = 'HR'
EMPLOYEE   = 'EM'

EXTERNAL_ROLE_CHOICES = (
    (HR_ADMIN,   _('HR Admin')),
    (HR,         _('HR')),
    (EMPLOYEE,   _('Employee')),
)

INTERNAL_ROLE_CHOICES = (
    (JURIST,    _('Jurist')),
    (CONSULTANT, _('Consultant')),
)

ALL_ROLE_CHOICES = (
    (JURIST,    _('Jurist')),
    (CONSULTANT, _('Consultant')),
    (HR_ADMIN,   _('HR Admin')),
    (HR,         _('HR')),
    (EMPLOYEE,   _('Employee')),
)

def get_internal_roles():
    roles = []
    for r in INTERNAL_ROLE_CHOICES:
        roles.append(r[0])
    return roles

def get_external_roles():
    roles = []
    for r in EXTERNAL_ROLE_CHOICES:
        roles.append(r[0])
    return roles

def get_hr_roles():
    return [HR, HR_ADMIN]

def get_jurist_queryset():
    return User.objects.filter(role__exact=JURIST)

def get_consultant_queryset():
    return User.objects.filter(role__exact=CONSULTANT)

def get_local_user_queryset():
    return get_jurist_queryset()|get_consultant_queryset()

def get_employee_user_queryset():
    return User.objects.filter(role__exact=EMPLOYEE)

def get_hr_user_queryset():
    return User.objects.filter(role__exact=HR)|User.objects.filter(role__exact=HR_ADMIN)

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

class User(AbstractUser):
    # changes email to unique and blank to false
    USERNAME_FIELD = 'email'
    email = models.EmailField(unique=True)

    # removes username from REQUIRED_FIELDS
    REQUIRED_FIELDS = []
    username = models.CharField(max_length=1, blank=True, null=True,
                                default=None)

    role = models.CharField(max_length=2, choices=ALL_ROLE_CHOICES,
                            default=JURIST)
    billing = models.BooleanField(default=False)
    objects = UserManager()
    token = models.CharField(max_length=64, default="", blank=True)
    token_date = models.DateTimeField(null=True)
    password_last_update = models.DateField(blank=True, null=True)
    GDPR_accepted = models.BooleanField(default=None, null=True)
    responsible = models.ManyToManyField("self", blank=True)
    hr_employees = models.ManyToManyField("self", blank=True,
                                          related_name='hr_employee_set')
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES,
                                default=ENGLISH)
    company = models.CharField(max_length=50, blank=True)

    def __str__(self):
        if self.first_name != '' or self.last_name != '':
            return self.first_name + ' ' + self.last_name
        return ''

class UserOldPasswords(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    password = models.CharField(max_length=50)
