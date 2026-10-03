"""
SERENIA ACCOUNTING — ledger/urls_vouchers.py
===============================================
Vouchers reuse the JournalEntry model (voucher_type field
distinguishes Payment/Receipt/Contra/Sales/Purchase/etc.).
Routes for /api/v1/vouchers/ — alias of journal entries
filtered by voucher_type, for frontend convenience.
"""

from rest_framework.routers import DefaultRouter
from apps.ledger.views import JournalEntryViewSet

router = DefaultRouter()
router.register(r'', JournalEntryViewSet, basename='voucher')

urlpatterns = router.urls
