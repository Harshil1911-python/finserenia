"""
SERENIA ACCOUNTING — ledger/urls_journals.py
===============================================
Routes for /api/v1/journals/
"""

from rest_framework.routers import DefaultRouter
from apps.ledger.views import JournalEntryViewSet

router = DefaultRouter()
router.register(r'', JournalEntryViewSet, basename='journal-entry')

urlpatterns = router.urls
