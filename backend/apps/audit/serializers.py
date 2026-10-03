"""
SERENIA ACCOUNTING — audit/serializers.py
=============================================
AuditPlan, RiskAssessment, WorkingPaper, ComplianceChecklistItem,
AuditObservation serializers and viewsets.
Access restricted to CA / Auditor / Admin / Super Admin (CanAccessAuditModule).
"""

from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.audit.models import AuditPlan, RiskAssessment, WorkingPaper, ComplianceChecklistItem, AuditObservation
from apps.ledger.views import CompanyScopedViewSet
from apps.core.permissions import CanAccessAuditModule, CompanyPermission
from rest_framework.permissions import IsAuthenticated


class RiskAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAssessment
        fields = '__all__'
        read_only_fields = ['id', 'assessed_by', 'created_at']


class WorkingPaperSerializer(serializers.ModelSerializer):
    prepared_by_name = serializers.CharField(source='prepared_by.get_full_name', read_only=True, allow_null=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = WorkingPaper
        fields = '__all__'
        read_only_fields = ['id', 'prepared_by', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']


class ComplianceChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceChecklistItem
        fields = '__all__'
        read_only_fields = ['id', 'checked_by', 'checked_at']


class AuditObservationSerializer(serializers.ModelSerializer):
    raised_by_name = serializers.CharField(source='raised_by.get_full_name', read_only=True, allow_null=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = AuditObservation
        fields = '__all__'
        read_only_fields = ['id', 'raised_by', 'resolved_at', 'created_at', 'updated_at']


class AuditPlanSerializer(serializers.ModelSerializer):
    lead_auditor_name = serializers.CharField(source='lead_auditor.get_full_name', read_only=True, allow_null=True)
    financial_year_label = serializers.CharField(source='financial_year.label', read_only=True)
    risk_assessments = RiskAssessmentSerializer(many=True, read_only=True)
    checklist_items = ComplianceChecklistItemSerializer(many=True, read_only=True)
    observation_count = serializers.SerializerMethodField()
    open_observation_count = serializers.SerializerMethodField()

    class Meta:
        model = AuditPlan
        fields = '__all__'
        read_only_fields = ['id', 'company', 'created_by', 'created_at', 'updated_at']

    def get_observation_count(self, obj):
        return obj.observations.count()

    def get_open_observation_count(self, obj):
        return obj.observations.exclude(status__in=['resolved', 'closed']).count()


# ── ViewSets ──────────────────────────────────────────────────
class AuditPlanViewSet(CompanyScopedViewSet):
    serializer_class = AuditPlanSerializer
    permission_classes = [IsAuthenticated, CompanyPermission, CanAccessAuditModule]
    filterset_fields = ['status', 'audit_type', 'financial_year']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = AuditPlan.objects.filter(company_id=company_id) if company_id else AuditPlan.objects.none()
        return qs.select_related('financial_year', 'lead_auditor').prefetch_related('risk_assessments', 'checklist_items', 'observations')

    def perform_create(self, serializer):
        serializer.save(company_id=self.get_company_id(), created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """Generates a consolidated audit report summary."""
        plan = self.get_object()
        observations = plan.observations.all()

        return Response({
            'plan': AuditPlanSerializer(plan).data,
            'summary': {
                'total_observations': observations.count(),
                'by_severity': {
                    sev: observations.filter(severity=sev).count()
                    for sev, _ in AuditObservation.SEVERITY
                },
                'by_status': {
                    st: observations.filter(status=st).count()
                    for st, _ in AuditObservation.STATUS
                },
                'compliance_summary': {
                    st: plan.checklist_items.filter(status=st).count()
                    for st, _ in ComplianceChecklistItem.STATUS
                },
            },
        })


class RiskAssessmentViewSet(CompanyScopedViewSet):
    serializer_class = RiskAssessmentSerializer
    permission_classes = [IsAuthenticated, CompanyPermission, CanAccessAuditModule]
    company_field = None  # Scoped via audit_plan, not directly

    def get_queryset(self):
        company_id = self.get_company_id()
        return RiskAssessment.objects.filter(audit_plan__company_id=company_id) if company_id else RiskAssessment.objects.none()

    def perform_create(self, serializer):
        serializer.save(assessed_by=self.request.user)


class WorkingPaperViewSet(CompanyScopedViewSet):
    serializer_class = WorkingPaperSerializer
    permission_classes = [IsAuthenticated, CompanyPermission, CanAccessAuditModule]
    company_field = None

    def get_queryset(self):
        company_id = self.get_company_id()
        return WorkingPaper.objects.filter(audit_plan__company_id=company_id) if company_id else WorkingPaper.objects.none()

    def perform_create(self, serializer):
        serializer.save(prepared_by=self.request.user)

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        from django.utils import timezone
        paper = self.get_object()
        paper.status = 'reviewed'
        paper.reviewed_by = request.user
        paper.reviewed_at = timezone.now()
        paper.review_comments = request.data.get('comments', '')
        paper.save()
        return Response(WorkingPaperSerializer(paper).data)


class ComplianceChecklistItemViewSet(CompanyScopedViewSet):
    serializer_class = ComplianceChecklistItemSerializer
    permission_classes = [IsAuthenticated, CompanyPermission, CanAccessAuditModule]
    company_field = None

    def get_queryset(self):
        company_id = self.get_company_id()
        return ComplianceChecklistItem.objects.filter(audit_plan__company_id=company_id) if company_id else ComplianceChecklistItem.objects.none()

    @action(detail=True, methods=['post'])
    def mark_checked(self, request, pk=None):
        from django.utils import timezone
        item = self.get_object()
        item.status = request.data.get('status', 'compliant')
        item.remarks = request.data.get('remarks', '')
        item.checked_by = request.user
        item.checked_at = timezone.now()
        item.save()
        return Response(ComplianceChecklistItemSerializer(item).data)


class AuditObservationViewSet(CompanyScopedViewSet):
    serializer_class = AuditObservationSerializer
    permission_classes = [IsAuthenticated, CompanyPermission, CanAccessAuditModule]
    company_field = None
    filterset_fields = ['status', 'severity', 'audit_plan']

    def get_queryset(self):
        company_id = self.get_company_id()
        return AuditObservation.objects.filter(audit_plan__company_id=company_id) if company_id else AuditObservation.objects.none()

    def perform_create(self, serializer):
        serializer.save(raised_by=self.request.user)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        from django.utils import timezone
        obs = self.get_object()
        obs.status = 'resolved'
        obs.resolved_at = timezone.now()
        obs.management_response = request.data.get('management_response', obs.management_response)
        obs.save()
        return Response(AuditObservationSerializer(obs).data)
