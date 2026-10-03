"""
SERENIA ACCOUNTING — ledger/urls_cost_centers.py
===================================================
Routes for /api/v1/cost-centers/
"""

from rest_framework.routers import DefaultRouter
from apps.ledger.views import CostCenterViewSet, ProjectViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'', CostCenterViewSet, basename='cost-center')

urlpatterns = router.urls
