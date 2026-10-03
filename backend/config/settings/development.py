"""
SERENIA ACCOUNTING — config/settings/development.py
=======================================================
Local development overrides. Use:
DJANGO_SETTINGS_MODULE=config.settings.development
"""

from .production import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ['*']

# Relax security for local HTTP development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Use console email backend locally
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Enable debug toolbar
INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa: F405
INTERNAL_IPS = ['127.0.0.1']

# Eager celery execution for easier local testing (optional)
CELERY_TASK_ALWAYS_EAGER = False
