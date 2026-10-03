"""
SERENIA ACCOUNTING — Django Settings (Production)
==================================================
Uses environment variables for all secrets.
Compatible with Render and Docker deployments.
"""

import os
from pathlib import Path
from datetime import timedelta
import dj_database_url
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Security ──────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# CSRF_TRUSTED_ORIGINS must include scheme (https://) and is required by
# Django 4+ for cross-origin POST requests (e.g. admin login) over HTTPS,
# such as the Render frontend posting to the Render API domain.
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# ── Applications ──────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    'axes',
    'drf_spectacular',
    'phonenumber_field',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',     # User auth & company management
    'apps.ledger',       # Chart of accounts, ledgers, journals
    'apps.inventory',    # Stock, warehouses, purchase/sales orders
    'apps.audit',        # Audit planning, working papers
    'apps.taxation',     # GST, TDS, TCS
    'apps.payroll',      # Employees, salary, payslips
    'apps.banking',      # Bank accounts, reconciliation
    'apps.reports',      # Report generation engine
    'apps.compliance',   # Regulatory compliance
    'apps.developer_mode',  # Super admin customization
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware ────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
    'apps.core.middleware.AuditLogMiddleware',
    'apps.core.middleware.CompanyContextMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# ── Templates ─────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# ── Database ──────────────────────────────────────────────────
from .database import DATABASES

# ── Redis Cache ───────────────────────────────────────────────
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'serenia',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Cache timeout constants
CACHE_TTL_DASHBOARD = 60 * 5       # 5 min
CACHE_TTL_LEDGER = 60 * 15         # 15 min
CACHE_TTL_REPORTS = 60 * 60        # 1 hour
CACHE_TTL_TRIAL_BALANCE = 60 * 10  # 10 min

# ── Sessions ──────────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 hours
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ── Authentication ────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── JWT ───────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# ── DRF ───────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '200/minute',
    },
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# ── CORS ──────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
    'x-company-id',  # Custom header for multi-company context
]

# ── Celery ────────────────────────────────────────────────────
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TASK_ROUTES = {
    'apps.reports.tasks.*': {'queue': 'reports'},
    'apps.payroll.tasks.*': {'queue': 'payroll'},
    'apps.core.tasks.*': {'queue': 'notifications'},
}
CELERY_TASK_ALWAYS_EAGER = False

# ── Email ─────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@serenia.app')

# ── Static & Media ────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Security Headers ──────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ── Axes (Brute Force Protection) ────────────────────────────
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
AXES_RESET_ON_SUCCESS = True

# ── API Docs ─────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'Serenia Accounting API',
    'DESCRIPTION': 'Enterprise Cloud ERP Platform API Documentation',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# ── Internationalization ──────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Application Config ────────────────────────────────────────
APP_NAME = config('APP_NAME', default='Serenia Accounting')
APP_TAGLINE = config('APP_TAGLINE', default='Smart Cloud ERP for Modern Businesses')
APP_VERSION = config('APP_VERSION', default='1.0.0')
DEFAULT_CURRENCY = config('DEFAULT_CURRENCY', default='INR')
DEFAULT_TAX_COUNTRY = config('DEFAULT_TAX_COUNTRY', default='IN')

# ── Feature Flags ─────────────────────────────────────────────
FEATURE_FLAGS = {
    'AUDIT_MODULE': config('ENABLE_AUDIT_MODULE', default=True, cast=bool),
    'PAYROLL_MODULE': config('ENABLE_PAYROLL_MODULE', default=True, cast=bool),
    'INVENTORY_MODULE': config('ENABLE_INVENTORY_MODULE', default=True, cast=bool),
    'BANKING_MODULE': config('ENABLE_BANKING_MODULE', default=True, cast=bool),
    'TAXATION_MODULE': config('ENABLE_TAXATION_MODULE', default=True, cast=bool),
    'COMPLIANCE_MODULE': config('ENABLE_COMPLIANCE_MODULE', default=True, cast=bool),
    'DEVELOPER_MODE': config('ENABLE_DEVELOPER_MODE', default=True, cast=bool),
}
