"""
SERENIA ACCOUNTING — compliance/urls.py
==========================================
Routes for /api/v1/compliance/
"""

from rest_framework.routers import DefaultRouter
from apps.compliance.serializers import ComplianceTaskViewSet

router = DefaultRouter()
router.register(r'tasks', ComplianceTaskViewSet, basename='compliance-task')

urlpatterns = router.urls
