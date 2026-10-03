"""
SERENIA ACCOUNTING — audit/urls.py
=====================================
Routes for /api/v1/audit/
"""

from rest_framework.routers import DefaultRouter
from apps.audit.serializers import (
    AuditPlanViewSet, RiskAssessmentViewSet, WorkingPaperViewSet,
    ComplianceChecklistItemViewSet, AuditObservationViewSet,
)

router = DefaultRouter()
router.register(r'plans', AuditPlanViewSet, basename='audit-plan')
router.register(r'risk-assessments', RiskAssessmentViewSet, basename='risk-assessment')
router.register(r'working-papers', WorkingPaperViewSet, basename='working-paper')
router.register(r'checklist-items', ComplianceChecklistItemViewSet, basename='compliance-checklist-item')
router.register(r'observations', AuditObservationViewSet, basename='audit-observation')

urlpatterns = router.urls
