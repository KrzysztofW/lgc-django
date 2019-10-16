"""
Django settings for lgc_base project.

Generated by 'django-admin startproject' using Django 2.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os, json
import common
from django.utils.translation import ugettext_lazy as _

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# SECURE_HSTS_SECONDS = 3600
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE_DIR, 'lgc_base/lgc-config.json')) as cfg:
    lgc_config = json.load(cfg)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = lgc_config['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOW_DEBUG_LOGIN = False
DEBUG_LOGIN_PASSWD = 'oisUd874J'

ALLOWED_HOSTS = ["2.2.2.2", "localhost", "192.168.0.11", "lgc.example.com"]
ALLOWED_SESSION_NOTIMEOUT_SUBNETS = ['127.0.0.1/32', '192.168.0.0/24']
SESSION_EXPIRATION = 1200

# Application definition

INSTALLED_APPS = [
    'common.apps.CommonConfig',
    'users.apps.UsersConfig',
    'lgc.apps.LgcConfig',
    'hr.apps.HrConfig',
    'employee.apps.EmployeeConfig',
    'crispy_forms',
    'django_countries',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jquery',
    'djangoformsetjs',
    'bootstrap_datepicker_plus',
    'lgc.templatetags',
    'django.contrib.humanize',
]

MIDDLEWARE = [
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'lgc.middleware.UserRolesCheck',
    'lgc.middleware.SqlLogger',
]

ROOT_URLCONF = 'lgc_base.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lgc_base.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'common.db_backend',
        'NAME': lgc_config['DB_NAME'],
        'USER': lgc_config['DB_USER'],
        'PASSWORD': lgc_config['DB_PASSWORD'],
        'HOST':'/var/run/mysqld/mysqld.sock',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

AUTH_USER_MODEL = 'users.User'

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

EMAIL_HOST = lgc_config['EMAIL_HOST']
EMAIL_PORT = lgc_config['EMAIL_PORT']
EMAIL_HOST_USER = lgc_config['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = lgc_config['EMAIL_HOST_PASSWORD']
EMAIL_USE_TLS = lgc_config['EMAIL_USE_TLS']
ADMINS = [('John Doe', 'admin@example.com')]
SERVER_EMAIL = 'no-reply@example.com'
REMAINDER_RESP = []
FIRST_REMAINDER_DELAY = 7
SECOND_REMAINDER_DELAY = 14

LOGFILE_NAME = '/tmp/lgc.log'
LOGFILE_SIZE = 1 << 20
LOGFILE_COUNT = 4

SQL_LOGFILE_NAME = '/tmp/sql.log'
SQL_LOGFILE_SIZE = 100 << 20
SQL_LOGFILE_COUNT = 10

LOGGER_LGC = 'lgc'
LOGGER_USER = 'user'
LOGGER_HR = 'hr'
LOGGER_EMPLOYEE = 'employee'
LOGGER_SQL = 'sql'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s] %(filename)s:%(lineno)s %(message)s",
            'datefmt' : "%Y-%m-%d %H:%M:%S"
        },
        'minimal': {
            'format' : "[%(asctime)s] [%(name)s] %(message)s",
            'datefmt' : "%Y-%m-%d %H:%M:%S"
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'filters': ['require_debug_true'],
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'sqllogfile': {
            'level':'INFO',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': SQL_LOGFILE_NAME,
            'maxBytes': SQL_LOGFILE_SIZE,
            'backupCount': SQL_LOGFILE_COUNT,
            'formatter': 'minimal',
        },
        'logfile': {
            'level':'INFO',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': LOGFILE_NAME,
            'maxBytes': LOGFILE_SIZE,
            'backupCount': LOGFILE_COUNT,
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        LOGGER_LGC: {
            'handlers': ['logfile', 'console', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
        LOGGER_USER: {
            'handlers': ['logfile', 'console', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
        LOGGER_HR: {
            'handlers': ['logfile', 'console', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
        LOGGER_EMPLOYEE: {
            'handlers': ['logfile', 'console', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
        LOGGER_SQL: {
            'handlers': ['sqllogfile'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LANGUAGES = [
    ('en', _('English')),
    ('fr', _('French')),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/management/lgc/static'
LOGIN_REDIRECT_URL = 'lgc-home'
LOGIN_URL = 'user-login'
CRISPY_TEMPLATE_PACK = 'bootstrap4'

SITE_URL = 'http://localhost:8000'
AUTH_TOKEN_EXPIRY = 48
AUTH_PASSWORD_EXPIRY = 3 * 30

MEDIA_ROOT= '/home/LGC-documents'
MEDIA_URL = '/docs/'
MAX_FILE_SIZE = 2 # in megabytes

EXPIRATIONS_NB_DAYS  = 90
INVOICE_REMINDER_EMAIL = ''
