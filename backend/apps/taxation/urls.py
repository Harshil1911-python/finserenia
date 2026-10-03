"""
SERENIA ACCOUNTING — taxation/urls.py
========================================
Routes for /api/v1/taxation/
"""

from rest_framework.routers import DefaultRouter
from apps.taxation.serializers import GSTTransactionViewSet, GSTRFilingViewSet, TDSTransactionViewSet

router = DefaultRouter()
router.register(r'gst-transactions', GSTTransactionViewSet, basename='gst-transaction')
router.register(r'gstr-filings', GSTRFilingViewSet, basename='gstr-filing')
router.register(r'tds-transactions', TDSTransactionViewSet, basename='tds-transaction')

urlpatterns = router.urls
