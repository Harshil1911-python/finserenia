"""
SERENIA ACCOUNTING — ledger/views.py
========================================
ViewSets for LedgerGroup, Ledger, JournalEntry, CostCenter, Project.
All queries are scoped to the active company (X-Company-Id header).
Ledger list/dashboard caching invalidated on writes.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from django.db.models import Q

from apps.accounts.models import AuditLog
from apps.core.permissions import CompanyPermission, CanApproveVouchers, IsReadOnlyOrViewerSafe
from apps.ledger.models import LedgerGroup, Ledger, JournalEntry, CostCenter, Project, CurrencyRate, VoucherStatus
from apps.ledger.serializers import (
    LedgerGroupSerializer, LedgerGroupTreeSerializer, LedgerSerializer,
    JournalEntrySerializer, CostCenterSerializer, ProjectSerializer, CurrencyRateSerializer,
)


class CompanyScopedViewSet(viewsets.ModelViewSet):
    """Base class: filters queryset by X-Company-Id and auto-sets company on create."""
    permission_classes = [IsAuthenticated, CompanyPermission, IsReadOnlyOrViewerSafe]
    company_field = 'company'

    def get_company_id(self):
        return self.request.headers.get('X-Company-Id')

    def perform_create(self, serializer):
        serializer.save(**{self.company_field: self.get_company_id()})


class LedgerGroupViewSet(CompanyScopedViewSet):
    serializer_class = LedgerGroupSerializer

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = LedgerGroup.objects.filter(company_id=company_id) if company_id else LedgerGroup.objects.none()
        return qs.select_related('parent').order_by('sort_order', 'name')

    def list(self, request, *args, **kwargs):
        if request.query_params.get('tree') == 'true':
            roots = self.get_queryset().filter(parent__isnull=True)
            return Response(LedgerGroupTreeSerializer(roots, many=True).data)
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_system_group:
            return Response({'error': 'System account groups cannot be deleted.'}, status=status.HTTP_400_BAD_REQUEST)
        if instance.ledgers.exists() or instance.children.exists():
            return Response({'error': 'Cannot delete a group that has ledgers or sub-groups.'}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)


class LedgerViewSet(CompanyScopedViewSet):
    serializer_class = LedgerSerializer
    filterset_fields = ['is_party_ledger', 'is_bank_account', 'is_active', 'group']
    search_fields = ['name', 'code', 'alias', 'gstin', 'contact_name']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = Ledger.objects.filter(company_id=company_id) if company_id else Ledger.objects.none()
        qs = qs.select_related('group')

        nature = self.request.query_params.get('nature')
        if nature:
            qs = qs.filter(group__nature=nature)

        return qs.order_by('group__sort_order', 'name')

    def perform_create(self, serializer):
        super().perform_create(serializer)
        self._invalidate_dashboard_cache()

    def perform_update(self, serializer):
        serializer.save()
        self._invalidate_dashboard_cache()

    def _invalidate_dashboard_cache(self):
        company_id = self.get_company_id()
        cache.delete(f"dashboard_summary:{company_id}")
        cache.delete_pattern(f"trial_balance:{company_id}:*") if hasattr(cache, 'delete_pattern') else None

    @action(detail=True, methods=['get'])
    def reconcile_statement(self, request, pk=None):
        """Returns transactions for bank reconciliation matching."""
        ledger = self.get_object()
        if not ledger.is_bank_account:
            return Response({'error': 'Reconciliation is only available for bank ledgers.'}, status=status.HTTP_400_BAD_REQUEST)

        lines = ledger.journal_lines.filter(
            journal__status__in=[VoucherStatus.APPROVED, VoucherStatus.POSTED]
        ).select_related('journal').order_by('-journal__date')[:200]

        data = [{
            'journal_id': str(l.journal.id),
            'date': str(l.journal.date),
            'voucher_number': l.journal.voucher_number,
            'narration': l.journal.narration,
            'debit': str(l.debit_amount),
            'credit': str(l.credit_amount),
            'reference': l.journal.reference,
        } for l in lines]

        return Response(data)


class JournalEntryViewSet(CompanyScopedViewSet):
    serializer_class = JournalEntrySerializer
    filterset_fields = ['voucher_type', 'status']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = JournalEntry.objects.filter(company_id=company_id) if company_id else JournalEntry.objects.none()
        qs = qs.select_related('party', 'financial_year').prefetch_related('lines__ledger')

        date_after = self.request.query_params.get('date_after')
        date_before = self.request.query_params.get('date_before')
        if date_after:
            qs = qs.filter(date__gte=date_after)
        if date_before:
            qs = qs.filter(date__lte=date_before)

        return qs.order_by('-date', '-created_at')

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user, company=instance.company, action='create_journal_entry',
            model_name='JournalEntry', object_id=str(instance.id), object_repr=f"{instance.voucher_type} #{instance.voucher_number}",
            changes={'status': instance.status, 'total': str(instance.total_amount)},
        )
        self._invalidate_caches(instance.company_id)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_caches(instance.company_id)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CompanyPermission, CanApproveVouchers])
    def approve(self, request, pk=None):
        """Approve a pending journal entry and post it to the ledger."""
        journal = self.get_object()
        if journal.status != VoucherStatus.PENDING_APPROVAL:
            return Response({'error': 'Only entries pending approval can be approved.'}, status=status.HTTP_400_BAD_REQUEST)

        journal.post(posted_by=request.user)

        AuditLog.objects.create(
            user=request.user, company=journal.company, action='approve_journal_entry',
            model_name='JournalEntry', object_id=str(journal.id), object_repr=f"{journal.voucher_type} #{journal.voucher_number}",
            changes={'status': 'posted'},
        )
        self._invalidate_caches(journal.company_id)
        return Response(JournalEntrySerializer(journal).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CompanyPermission, CanApproveVouchers])
    def reject(self, request, pk=None):
        """Reject a pending journal entry."""
        journal = self.get_object()
        if journal.status != VoucherStatus.PENDING_APPROVAL:
            return Response({'error': 'Only entries pending approval can be rejected.'}, status=status.HTTP_400_BAD_REQUEST)

        journal.status = VoucherStatus.REJECTED
        journal.rejected_reason = request.data.get('reason', '')
        journal.save()

        AuditLog.objects.create(
            user=request.user, company=journal.company, action='reject_journal_entry',
            model_name='JournalEntry', object_id=str(journal.id), object_repr=f"{journal.voucher_type} #{journal.voucher_number}",
            changes={'status': 'rejected', 'reason': journal.rejected_reason},
        )
        return Response(JournalEntrySerializer(journal).data)

    def _invalidate_caches(self, company_id):
        cache.delete(f"dashboard_summary:{company_id}")


class CostCenterViewSet(CompanyScopedViewSet):
    serializer_class = CostCenterSerializer

    def get_queryset(self):
        company_id = self.get_company_id()
        return CostCenter.objects.filter(company_id=company_id) if company_id else CostCenter.objects.none()


class ProjectViewSet(CompanyScopedViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        company_id = self.get_company_id()
        return Project.objects.filter(company_id=company_id) if company_id else Project.objects.none()


class CurrencyRateViewSet(CompanyScopedViewSet):
    serializer_class = CurrencyRateSerializer

    def get_queryset(self):
        company_id = self.get_company_id()
        return CurrencyRate.objects.filter(company_id=company_id) if company_id else CurrencyRate.objects.none()
