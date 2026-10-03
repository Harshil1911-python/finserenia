"""
SERENIA ACCOUNTING — banking/urls.py
=======================================
Routes for /api/v1/banking/
"""

from rest_framework.routers import DefaultRouter
from apps.banking.serializers import BankStatementImportViewSet, BankStatementLineViewSet

router = DefaultRouter()
router.register(r'statement-imports', BankStatementImportViewSet, basename='bank-statement-import')
router.register(r'statement-lines', BankStatementLineViewSet, basename='bank-statement-line')

urlpatterns = router.urls
