"""
SERENIA ACCOUNTING — banking/serializers.py
==============================================
Bank statement import, line matching for reconciliation.
CSV parsing is done synchronously for small files; larger
files should be routed to a Celery task (see reports.tasks pattern).
"""

import csv
import io
from decimal import Decimal, InvalidOperation
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from apps.banking.models import BankStatementImport, BankStatementLine
from apps.ledger.views import CompanyScopedViewSet


class BankStatementLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankStatementLine
        fields = '__all__'
        read_only_fields = ['id', 'statement_import']


class BankStatementImportSerializer(serializers.ModelSerializer):
    bank_ledger_name = serializers.CharField(source='bank_ledger.name', read_only=True)
    lines = BankStatementLineSerializer(many=True, read_only=True)

    class Meta:
        model = BankStatementImport
        fields = '__all__'
        read_only_fields = ['id', 'company', 'status', 'total_records', 'matched_records', 'uploaded_by', 'created_at']


class BankStatementImportViewSet(CompanyScopedViewSet):
    serializer_class = BankStatementImportSerializer

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = BankStatementImport.objects.filter(company_id=company_id) if company_id else BankStatementImport.objects.none()
        return qs.select_related('bank_ledger').prefetch_related('lines').order_by('-created_at')

    def perform_create(self, serializer):
        instance = serializer.save(company_id=self.get_company_id(), uploaded_by=self.request.user)
        # CSV parsing handled separately via /upload-csv/ action
        return instance

    @action(detail=True, methods=['post'])
    def upload_csv(self, request, pk=None):
        """
        Expects multipart/form-data with 'file' field.
        CSV columns expected: date, description, reference, debit, credit, balance
        """
        statement_import = self.get_object()
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        decoded = io.TextIOWrapper(file.file, encoding='utf-8')
        reader = csv.DictReader(decoded)

        created_lines = []
        for row in reader:
            try:
                date_val = parse_date(row.get('date', '').strip())
                if not date_val:
                    continue
                debit = self._to_decimal(row.get('debit', '0'))
                credit = self._to_decimal(row.get('credit', '0'))
                balance = self._to_decimal(row.get('balance')) if row.get('balance') else None

                created_lines.append(BankStatementLine(
                    statement_import=statement_import, date=date_val,
                    description=row.get('description', '').strip()[:500],
                    reference=row.get('reference', '').strip()[:100],
                    debit=debit, credit=credit, balance=balance,
                ))
            except (ValueError, InvalidOperation):
                continue  # Skip malformed rows

        BankStatementLine.objects.bulk_create(created_lines)
        statement_import.total_records = len(created_lines)
        statement_import.status = 'completed'
        statement_import.save()

        # Auto-suggest matches
        self._auto_match(statement_import)

        return Response(BankStatementImportSerializer(statement_import).data)

    @staticmethod
    def _to_decimal(value):
        if value is None or str(value).strip() == '':
            return Decimal('0')
        return Decimal(str(value).replace(',', '').strip())

    @staticmethod
    def _auto_match(statement_import):
        """
        Suggests matches between bank statement lines and journal lines
        on the same bank ledger with matching amount and date (+/- 3 days).
        """
        from datetime import timedelta
        from apps.ledger.models import JournalLine, VoucherStatus

        candidate_lines = JournalLine.objects.filter(
            ledger=statement_import.bank_ledger,
            journal__status__in=[VoucherStatus.APPROVED, VoucherStatus.POSTED],
        ).select_related('journal')

        matched_count = 0
        for stmt_line in statement_import.lines.filter(match_status='unmatched'):
            amount = stmt_line.debit if stmt_line.debit else stmt_line.credit
            is_credit_in_books = stmt_line.debit > 0  # Money in (bank statement debit = inflow)

            for jl in candidate_lines:
                jl_amount = jl.debit_amount if is_credit_in_books else jl.credit_amount
                if jl_amount == amount and abs((jl.journal.date - stmt_line.date).days) <= 3:
                    stmt_line.match_status = 'suggested'
                    stmt_line.matched_journal_line = jl
                    stmt_line.save()
                    matched_count += 1
                    break

        statement_import.matched_records = matched_count
        statement_import.save(update_fields=['matched_records'])


class BankStatementLineViewSet(CompanyScopedViewSet):
    serializer_class = BankStatementLineSerializer
    filterset_fields = ['match_status', 'statement_import']

    def get_queryset(self):
        company_id = self.get_company_id()
        return BankStatementLine.objects.filter(
            statement_import__company_id=company_id
        ) if company_id else BankStatementLine.objects.none()

    @action(detail=True, methods=['post'])
    def confirm_match(self, request, pk=None):
        """Confirms a suggested match or sets a manual match to a journal line."""
        line = self.get_object()
        journal_line_id = request.data.get('journal_line_id')

        from django.utils import timezone
        from apps.ledger.models import JournalLine

        if journal_line_id:
            try:
                jl = JournalLine.objects.get(id=journal_line_id)
                line.matched_journal_line = jl
            except JournalLine.DoesNotExist:
                return Response({'error': 'Journal line not found'}, status=status.HTTP_404_NOT_FOUND)

        line.match_status = 'matched'
        line.matched_by = request.user
        line.matched_at = timezone.now()
        line.save()

        return Response(BankStatementLineSerializer(line).data)

    @action(detail=True, methods=['post'])
    def ignore(self, request, pk=None):
        line = self.get_object()
        line.match_status = 'ignored'
        line.save()
        return Response(BankStatementLineSerializer(line).data)
