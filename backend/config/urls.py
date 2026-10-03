"""
SERENIA ACCOUNTING — Main URL Configuration
===========================================
All API routes versioned under /api/v1/
Updated to use consolidated url files (no urls/ subdirectories).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerUIView

from apps.accounts.urls import auth_urlpatterns, company_router, user_router
from apps.core.urls import health_urlpatterns
from apps.core.urls_dashboard import dashboard_urlpatterns

urlpatterns = [
    # Django Admin
    path('django-admin/', admin.site.urls),

    # Health Check
    path('api/v1/health/', include(health_urlpatterns)),

    # Authentication
    path('api/v1/auth/', include(auth_urlpatterns)),

    # Company & User Management
    path('api/v1/companies/', include(company_router.urls)),
    path('api/v1/users/', include(user_router.urls)),

    # Chart of Accounts & Ledger
    path('api/v1/ledger/', include('apps.ledger.urls')),

    # Vouchers & Journal Entries
    path('api/v1/vouchers/', include('apps.ledger.urls_vouchers')),
    path('api/v1/journals/', include('apps.ledger.urls_journals')),

    # Financial Reports
    path('api/v1/reports/', include('apps.reports.urls')),

    # Taxation (GST / TDS / TCS)
    path('api/v1/taxation/', include('apps.taxation.urls')),

    # Payroll
    path('api/v1/payroll/', include('apps.payroll.urls')),

    # Inventory
    path('api/v1/inventory/', include('apps.inventory.urls')),

    # Banking
    path('api/v1/banking/', include('apps.banking.urls')),

    # Audit
    path('api/v1/audit/', include('apps.audit.urls')),

    # Compliance
    path('api/v1/compliance/', include('apps.compliance.urls')),

    # Cost Centers
    path('api/v1/cost-centers/', include('apps.ledger.urls_cost_centers')),

    # Dashboard
    path('api/v1/dashboard/', include(dashboard_urlpatterns)),

    # Developer Mode (Super Admin only)
    path('api/v1/developer/', include('apps.developer_mode.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerUIView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
