"""
SERENIA ACCOUNTING — inventory/urls.py
=========================================
Routes for /api/v1/inventory/
"""

from rest_framework.routers import DefaultRouter
from apps.inventory.serializers import (
    ItemViewSet, ItemCategoryViewSet, UnitViewSet, WarehouseViewSet,
    StockEntryViewSet, PurchaseOrderViewSet,
)

router = DefaultRouter()
router.register(r'items', ItemViewSet, basename='item')
router.register(r'categories', ItemCategoryViewSet, basename='item-category')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'stock-entries', StockEntryViewSet, basename='stock-entry')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')

urlpatterns = router.urls
