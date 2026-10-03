"""
SERENIA ACCOUNTING — core/urls.py
=====================================
Health check and dashboard routes.
Consolidated from urls/ subfolder to reduce file count.
"""

from django.urls import path
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache


def health_check(request):
    """
    Returns 200 if database and Redis are reachable.
    Used by Render's healthCheckPath and Docker HEALTHCHECK.
    """
    checks = {'database': False, 'cache': False}
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = True
    except Exception:
        pass
    try:
        cache.set('health_check', 'ok', 5)
        checks['cache'] = cache.get('health_check') == 'ok'
    except Exception:
        pass
    healthy = all(checks.values())
    return JsonResponse(
        {'status': 'healthy' if healthy else 'degraded', 'checks': checks},
        status=200 if healthy else 503,
    )


health_urlpatterns = [
    path('', health_check, name='health-check'),
]
