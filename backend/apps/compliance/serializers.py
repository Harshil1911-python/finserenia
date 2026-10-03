"""
SERENIA ACCOUNTING — compliance/serializers.py
==================================================
ComplianceTask serializer and viewset.
"""

from datetime import date, timedelta
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.compliance.models import ComplianceTask
from apps.ledger.views import CompanyScopedViewSet


class ComplianceTaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, allow_null=True)
    days_until_due = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceTask
        fields = '__all__'
        read_only_fields = ['id', 'company', 'completed_at', 'completed_by', 'created_at']

    def get_days_until_due(self, obj):
        return (obj.due_date - date.today()).days


class ComplianceTaskViewSet(CompanyScopedViewSet):
    serializer_class = ComplianceTaskSerializer
    filterset_fields = ['category', 'status', 'frequency']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = ComplianceTask.objects.filter(company_id=company_id) if company_id else ComplianceTask.objects.none()
        return qs.select_related('assigned_to')

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Returns tasks due within the next 30 days, plus overdue tasks."""
        today = date.today()
        qs = self.get_queryset().exclude(status='filed')
        upcoming = qs.filter(due_date__lte=today + timedelta(days=30)).order_by('due_date')

        # Mark overdue
        overdue_ids = [t.id for t in upcoming if t.due_date < today]
        if overdue_ids:
            ComplianceTask.objects.filter(id__in=overdue_ids).update(status='overdue')
            upcoming = qs.filter(due_date__lte=today + timedelta(days=30)).order_by('due_date')

        return Response(self.get_serializer(upcoming, many=True).data)

    @action(detail=True, methods=['post'])
    def mark_filed(self, request, pk=None):
        from django.utils import timezone
        task = self.get_object()
        task.status = 'filed'
        task.completed_at = timezone.now()
        task.completed_by = request.user
        task.reference_number = request.data.get('reference_number', task.reference_number)
        task.save()
        return Response(self.get_serializer(task).data)
