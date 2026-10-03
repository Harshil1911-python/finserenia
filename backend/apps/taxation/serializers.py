"""
SERENIA ACCOUNTING — taxation/serializers.py & views.py combined
====================================================================
GST transaction reporting, GSTR filings, TDS transactions.
"""

from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q
from apps.taxation.models import GSTTransaction, GSTRFiling, TDSTransaction
from apps.ledger.views import CompanyScopedViewSet


# ── Serializers ───────────────────────────────────────────────
class GSTTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSTTransaction
        fields = '__all__'
        read_only_fields = ['id', 'company', 'total_tax', 'created_at', 'updated_at']


class GSTRFilingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSTRFiling
        fields = '__all__'
        read_only_fields = ['id', 'company', 'created_at']


class TDSTransactionSerializer(serializers.ModelSerializer):
    deductee_ledger_name = serializers.CharField(source='deductee_ledger.name', read_only=True)

    class Meta:
        model = TDSTransaction
        fields = '__all__'
        read_only_fields = ['id', 'company', 'total_tax_deducted', 'created_at']


# ── ViewSets ──────────────────────────────────────────────────
class GSTTransactionViewSet(CompanyScopedViewSet):
    serializer_class = GSTTransactionSerializer
    filterset_fields = ['supply_type', 'gstr1_filed', 'gstr3b_filed']

    def get_queryset(self):
        company_id = self.get_company_id()
        return GSTTransaction.objects.filter(company_id=company_id) if company_id else GSTTransaction.objects.none()

    @action(detail=False, methods=['get'])
    def gstr1_summary(self, request):
        """
        Summarized GSTR-1 data grouped by supply type for a given period (MMYYYY).
        """
        period = request.query_params.get('period')
        qs = self.get_queryset()
        if period:
            qs = qs.filter(invoice_date__isnull=False, gstr1_period=period)

        summary = qs.values('supply_type').annotate(
            taxable_value=Sum('taxable_value'),
            igst=Sum('igst_amount'),
            cgst=Sum('cgst_amount'),
            sgst=Sum('sgst_amount'),
            cess=Sum('cess_amount'),
            count=Sum(1),
        )
        return Response(list(summary))

    @action(detail=False, methods=['get'])
    def gstr3b_summary(self, request):
        """
        GSTR-3B summary: outward tax liability vs input tax credit.
        """
        period = request.query_params.get('period')
        qs = self.get_queryset()
        if period:
            qs = qs.filter(gstr3b_period=period)

        outward = qs.exclude(supply_type='cdn').aggregate(
            taxable_value=Sum('taxable_value'), igst=Sum('igst_amount'),
            cgst=Sum('cgst_amount'), sgst=Sum('sgst_amount'), cess=Sum('cess_amount'),
        )
        itc = qs.filter(is_itc_eligible=True).aggregate(
            igst=Sum('igst_amount'), cgst=Sum('cgst_amount'), sgst=Sum('sgst_amount'), cess=Sum('cess_amount'),
        )
        return Response({'outward_supplies': outward, 'eligible_itc': itc})


class GSTRFilingViewSet(CompanyScopedViewSet):
    serializer_class = GSTRFilingSerializer
    filterset_fields = ['return_type', 'status', 'period']

    def get_queryset(self):
        company_id = self.get_company_id()
        return GSTRFiling.objects.filter(company_id=company_id) if company_id else GSTRFiling.objects.none()

    @action(detail=True, methods=['post'])
    def mark_filed(self, request, pk=None):
        from django.utils import timezone
        filing = self.get_object()
        filing.status = 'filed'
        filing.arn_number = request.data.get('arn_number', '')
        filing.filing_date = timezone.now()
        filing.filed_by = request.user
        filing.save()
        return Response(GSTRFilingSerializer(filing).data)


class TDSTransactionViewSet(CompanyScopedViewSet):
    serializer_class = TDSTransactionSerializer
    filterset_fields = ['section', 'is_deposited', 'tds_return_filed']

    def get_queryset(self):
        company_id = self.get_company_id()
        return TDSTransaction.objects.filter(company_id=company_id) if company_id else TDSTransaction.objects.none()

    @action(detail=False, methods=['get'])
    def section_summary(self, request):
        """TDS liability grouped by section, for return filing."""
        qs = self.get_queryset()
        summary = qs.values('section').annotate(
            total_payment=Sum('payment_amount'),
            total_tds=Sum('total_tax_deducted'),
        )
        return Response(list(summary))
