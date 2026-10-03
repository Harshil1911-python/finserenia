"""
SERENIA ACCOUNTING — ledger/urls.py
=======================================
Routes for /api/v1/ledger/
"""

from rest_framework.routers import DefaultRouter
from apps.ledger.views import LedgerGroupViewSet, LedgerViewSet, CurrencyRateViewSet

router = DefaultRouter()
router.register(r'groups', LedgerGroupViewSet, basename='ledger-group')
router.register(r'ledgers', LedgerViewSet, basename='ledger')
router.register(r'currency-rates', CurrencyRateViewSet, basename='currency-rate')

urlpatterns = router.urls
