"""
SERENIA ACCOUNTING — ledger/serializers.py
=============================================
Serializers for LedgerGroup, Ledger, JournalEntry, JournalLine,
CostCenter, Project, CurrencyRate.
"""

from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from apps.ledger.models import (
    LedgerGroup, Ledger, JournalEntry, JournalLine, CostCenter, Project,
    CurrencyRate, VoucherStatus,
)


# ── Ledger Group ──────────────────────────────────────────────
class LedgerGroupSerializer(serializers.ModelSerializer):
    full_path = serializers.CharField(read_only=True)
    ledger_count = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)

    class Meta:
        model = LedgerGroup
        fields = [
            'id', 'company', 'name', 'code', 'nature', 'group_type',
            'parent', 'parent_name', 'affects_gross_profit', 'is_system_group',
            'sort_order', 'description', 'full_path', 'ledger_count',
        ]
        read_only_fields = ['id', 'company', 'is_system_group']

    def get_ledger_count(self, obj):
        return obj.ledgers.filter(is_active=True).count()


class LedgerGroupTreeSerializer(serializers.ModelSerializer):
    """Recursive serializer for hierarchical tree display."""
    children = serializers.SerializerMethodField()
    ledger_count = serializers.SerializerMethodField()

    class Meta:
        model = LedgerGroup
        fields = ['id', 'name', 'code', 'nature', 'group_type', 'parent', 'affects_gross_profit', 'children', 'ledger_count']

    def get_children(self, obj):
        children = obj.children.all().order_by('sort_order', 'name')
        return LedgerGroupTreeSerializer(children, many=True).data

    def get_ledger_count(self, obj):
        return obj.ledgers.filter(is_active=True).count()


# ── Ledger ────────────────────────────────────────────────────
class LedgerSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    nature = serializers.CharField(source='group.nature', read_only=True)
    current_balance = serializers.SerializerMethodField()
    current_balance_type = serializers.SerializerMethodField()

    class Meta:
        model = Ledger
        fields = [
            'id', 'company', 'group', 'group_name', 'nature', 'name', 'code', 'alias',
            'gstin', 'gst_registration_type', 'is_tds_applicable', 'tds_rate', 'tds_section',
            'opening_balance', 'opening_balance_type', 'opening_balance_date',
            'is_party_ledger', 'contact_name', 'email', 'phone', 'address',
            'credit_limit', 'credit_days',
            'is_bank_account', 'bank_name', 'account_number', 'ifsc_code', 'branch_name',
            'currency', 'is_active', 'is_system_ledger', 'description',
            'created_at', 'updated_at', 'current_balance', 'current_balance_type',
        ]
        read_only_fields = ['id', 'company', 'is_system_ledger', 'created_at', 'updated_at']

    def get_current_balance(self, obj):
        balance = obj.get_balance()
        return str(abs(balance))

    def get_current_balance_type(self, obj):
        balance = obj.get_balance()
        return 'Dr' if balance >= 0 else 'Cr'

    def validate_group(self, value):
        # Ensure group belongs to the same company
        company_id = self.context['request'].headers.get('X-Company-Id')
        if str(value.company_id) != str(company_id):
            raise serializers.ValidationError("Selected group does not belong to the active company.")
        return value


# ── Journal Line ──────────────────────────────────────────────
class JournalLineSerializer(serializers.ModelSerializer):
    ledger_name = serializers.CharField(source='ledger.name', read_only=True)

    class Meta:
        model = JournalLine
        fields = [
            'id', 'ledger', 'ledger_name', 'debit_amount', 'credit_amount',
            'foreign_currency', 'foreign_amount', 'gst_category', 'tax_rate',
            'cost_center', 'project', 'narration', 'sort_order',
        ]
        read_only_fields = ['id']


# ── Journal Entry ─────────────────────────────────────────────
class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True)
    party_name = serializers.CharField(source='party.name', read_only=True, allow_null=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = [
            'id', 'company', 'financial_year', 'branch', 'voucher_type', 'voucher_number',
            'date', 'narration', 'reference', 'party', 'party_name', 'status',
            'approved_by', 'approved_at', 'rejected_reason', 'currency', 'exchange_rate',
            'is_gst_transaction', 'gst_data', 'is_recurring', 'recurring_config',
            'attachments', 'lines', 'total_amount', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'company', 'financial_year', 'voucher_number', 'approved_by', 'approved_at',
            'rejected_reason', 'created_by', 'created_at', 'updated_at',
        ]

    def get_total_amount(self, obj):
        return str(sum((l.debit_amount for l in obj.lines.all()), Decimal('0')))

    def validate_lines(self, lines):
        if len(lines) < 2:
            raise serializers.ValidationError("A journal entry requires at least two lines.")

        total_dr = sum((Decimal(str(l.get('debit_amount', 0) or 0)) for l in lines), Decimal('0'))
        total_cr = sum((Decimal(str(l.get('credit_amount', 0) or 0)) for l in lines), Decimal('0'))

        if total_dr != total_cr:
            raise serializers.ValidationError(
                f"Entry is not balanced. Total Debit: {total_dr}, Total Credit: {total_cr}."
            )
        if total_dr == 0:
            raise serializers.ValidationError("Entry amounts cannot all be zero.")

        for line in lines:
            dr = Decimal(str(line.get('debit_amount', 0) or 0))
            cr = Decimal(str(line.get('credit_amount', 0) or 0))
            if dr > 0 and cr > 0:
                raise serializers.ValidationError("A line cannot have both debit and credit amounts.")
            if dr == 0 and cr == 0:
                raise serializers.ValidationError("Each line must have a non-zero debit or credit amount.")

        return lines

    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        request = self.context['request']
        company_id = request.headers.get('X-Company-Id')

        from apps.accounts.models import Company

        company = Company.objects.get(id=company_id)
        fy = company.current_financial_year
        if not fy:
            raise serializers.ValidationError("No active financial year found for this company.")
        if fy.is_closed:
            raise serializers.ValidationError("The current financial year is closed for postings.")

        # Generate voucher number: <TYPE>-<FY>-<sequence>
        voucher_type = validated_data['voucher_type']
        prefix = voucher_type.upper()[:3]
        existing_count = JournalEntry.objects.filter(
            company=company, voucher_type=voucher_type, financial_year=fy
        ).count()
        voucher_number = f"{prefix}-{fy.label.replace('FY ', '')}-{existing_count + 1:05d}"

        journal = JournalEntry.objects.create(
            company=company, financial_year=fy, voucher_number=voucher_number,
            created_by=request.user, **validated_data,
        )

        for idx, line_data in enumerate(lines_data):
            JournalLine.objects.create(journal=journal, sort_order=idx, **line_data)

        return journal

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.status in [VoucherStatus.POSTED, VoucherStatus.APPROVED]:
            raise serializers.ValidationError("Cannot edit a posted or approved journal entry. Create a reversing entry instead.")

        lines_data = validated_data.pop('lines', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lines_data is not None:
            instance.lines.all().delete()
            for idx, line_data in enumerate(lines_data):
                JournalLine.objects.create(journal=instance, sort_order=idx, **line_data)

        return instance


# ── Cost Center / Project ─────────────────────────────────────
class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = '__all__'
        read_only_fields = ['id', 'company', 'created_at']


class ProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True, allow_null=True)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'company', 'created_at']


class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = '__all__'
        read_only_fields = ['id', 'company', 'created_at']
