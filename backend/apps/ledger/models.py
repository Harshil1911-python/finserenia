"""
SERENIA ACCOUNTING — ledger/models.py
======================================
Chart of Accounts, Account Groups, Ledgers,
Journal Entries, Vouchers, Cost Centers, and Multi-Currency.

Double-entry bookkeeping enforced at model level:
Every JournalEntry must have balanced Debit = Credit.
"""

import uuid
from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import User, Company, Branch, FinancialYear


# ── Account Group Constants ───────────────────────────────────
class AccountNature(models.TextChoices):
    ASSETS = 'assets', 'Assets'
    LIABILITIES = 'liabilities', 'Liabilities'
    CAPITAL = 'capital', 'Capital & Equity'
    INCOME = 'income', 'Income / Revenue'
    EXPENSES = 'expenses', 'Expenses'


class AccountGroup(models.TextChoices):
    # Assets
    CURRENT_ASSETS = 'current_assets', 'Current Assets'
    FIXED_ASSETS = 'fixed_assets', 'Fixed Assets'
    INVESTMENTS = 'investments', 'Investments'
    LOANS_ADVANCES = 'loans_advances', 'Loans & Advances'
    # Liabilities
    CURRENT_LIABILITIES = 'current_liabilities', 'Current Liabilities'
    LONG_TERM_LIABILITIES = 'long_term_liabilities', 'Long-term Liabilities'
    # Capital
    SHARE_CAPITAL = 'share_capital', 'Share Capital'
    RESERVES_SURPLUS = 'reserves_surplus', 'Reserves & Surplus'
    # Income
    SALES = 'sales', 'Sales / Revenue'
    OTHER_INCOME = 'other_income', 'Other Income'
    # Expenses
    PURCHASE = 'purchase', 'Purchases'
    DIRECT_EXPENSES = 'direct_expenses', 'Direct Expenses'
    INDIRECT_EXPENSES = 'indirect_expenses', 'Indirect Expenses'
    DEPRECIATION = 'depreciation', 'Depreciation'


class VoucherType(models.TextChoices):
    PAYMENT = 'payment', 'Payment'
    RECEIPT = 'receipt', 'Receipt'
    CONTRA = 'contra', 'Contra'
    JOURNAL = 'journal', 'Journal'
    SALES = 'sales', 'Sales'
    PURCHASE = 'purchase', 'Purchase'
    CREDIT_NOTE = 'credit_note', 'Credit Note'
    DEBIT_NOTE = 'debit_note', 'Debit Note'
    OPENING_BALANCE = 'opening_balance', 'Opening Balance'


class VoucherStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING_APPROVAL = 'pending_approval', 'Pending Approval'
    APPROVED = 'approved', 'Approved'
    POSTED = 'posted', 'Posted'
    REJECTED = 'rejected', 'Rejected'
    CANCELLED = 'cancelled', 'Cancelled'


# ── Account Group Hierarchy ───────────────────────────────────
class LedgerGroup(models.Model):
    """
    Hierarchical grouping for Chart of Accounts.
    Supports unlimited nesting. Parent=None means it's a root group.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ledger_groups')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, blank=True)
    nature = models.CharField(max_length=20, choices=AccountNature.choices)
    group_type = models.CharField(max_length=30, choices=AccountGroup.choices, blank=True)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')

    # Affects balance sheet/P&L grouping
    affects_gross_profit = models.BooleanField(default=False)
    is_system_group = models.BooleanField(default=False)  # Built-in, cannot delete

    sort_order = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ledger_groups'
        unique_together = ['company', 'name']
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.company.name} — {self.name}"

    @property
    def full_path(self):
        """Returns full hierarchy path: Assets > Current Assets > Cash"""
        parts = [self.name]
        parent = self.parent
        while parent:
            parts.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(parts)


# ── Ledger (Individual Account) ───────────────────────────────
class Ledger(models.Model):
    """
    Individual account in Chart of Accounts.
    Belongs to a LedgerGroup. Has opening balance.
    All transactions reference a ledger.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ledgers')
    group = models.ForeignKey(LedgerGroup, on_delete=models.PROTECT, related_name='ledgers')
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=20, blank=True, db_index=True)
    alias = models.CharField(max_length=255, blank=True)

    # GST related
    gstin = models.CharField(max_length=15, blank=True)
    gst_registration_type = models.CharField(max_length=30, blank=True)

    # TDS / TCS
    is_tds_applicable = models.BooleanField(default=False)
    tds_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    tds_section = models.CharField(max_length=20, blank=True)

    # Opening balance
    opening_balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    opening_balance_type = models.CharField(max_length=6, choices=[('Dr', 'Debit'), ('Cr', 'Credit')], default='Dr')
    opening_balance_date = models.DateField(null=True, blank=True)

    # Contact info (for party ledgers — customers, suppliers)
    is_party_ledger = models.BooleanField(default=False)
    contact_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    credit_limit = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    credit_days = models.IntegerField(default=0)

    # Bank details (for bank ledgers)
    is_bank_account = models.BooleanField(default=False)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=30, blank=True)
    ifsc_code = models.CharField(max_length=11, blank=True)
    branch_name = models.CharField(max_length=100, blank=True)

    # Currency
    currency = models.CharField(max_length=3, default='INR')

    is_active = models.BooleanField(default=True)
    is_system_ledger = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ledgers'
        unique_together = ['company', 'name']
        indexes = [
            models.Index(fields=['company', 'name']),
            models.Index(fields=['company', 'code']),
            models.Index(fields=['is_party_ledger']),
            models.Index(fields=['is_bank_account']),
        ]

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    def get_balance(self, financial_year=None, as_of_date=None):
        """Calculate current balance from journal lines."""
        from django.db.models import Sum, Q
        qs = self.journal_lines.filter(
            journal__status__in=[VoucherStatus.APPROVED, VoucherStatus.POSTED]
        )
        if financial_year:
            qs = qs.filter(journal__financial_year=financial_year)
        if as_of_date:
            qs = qs.filter(journal__date__lte=as_of_date)

        result = qs.aggregate(
            total_debit=Sum('debit_amount'),
            total_credit=Sum('credit_amount')
        )
        dr = result['total_debit'] or Decimal('0')
        cr = result['total_credit'] or Decimal('0')
        return dr - cr + self.opening_balance


# ── Journal Entry (Main Transaction) ──────────────────────────
class JournalEntry(models.Model):
    """
    Core accounting transaction. Implements double-entry bookkeeping.
    Must always have balanced debit = credit across all lines.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_entries')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name='journal_entries')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)

    # Voucher linkage
    voucher_type = models.CharField(max_length=20, choices=VoucherType.choices)
    voucher_number = models.CharField(max_length=50, db_index=True)
    date = models.DateField(db_index=True)

    # Reference
    narration = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True)  # Invoice/cheque number
    party = models.ForeignKey(Ledger, on_delete=models.SET_NULL, null=True, blank=True, related_name='party_journals')

    # Status & Approval
    status = models.CharField(max_length=25, choices=VoucherStatus.choices, default=VoucherStatus.DRAFT)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_journals')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.TextField(blank=True)

    # Currency
    currency = models.CharField(max_length=3, default='INR')
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal('1'))

    # GST
    is_gst_transaction = models.BooleanField(default=False)
    gst_data = models.JSONField(default=dict)

    # Recurring
    is_recurring = models.BooleanField(default=False)
    recurring_config = models.JSONField(default=dict)
    parent_recurring = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    # Attachments
    attachments = models.JSONField(default=list)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_journals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'journal_entries'
        unique_together = ['company', 'voucher_type', 'voucher_number']
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['company', 'date']),
            models.Index(fields=['company', 'voucher_type', 'date']),
            models.Index(fields=['status']),
            models.Index(fields=['financial_year', 'date']),
        ]

    def __str__(self):
        return f"{self.voucher_type.upper()} #{self.voucher_number} — {self.date}"

    @property
    def total_amount(self):
        return self.lines.aggregate(
            total=models.Sum('debit_amount')
        )['total'] or Decimal('0')

    def clean(self):
        """Ensure debit = credit (double-entry rule)."""
        if self.pk:
            lines = self.lines.all()
            total_dr = sum(l.debit_amount for l in lines)
            total_cr = sum(l.credit_amount for l in lines)
            if total_dr != total_cr:
                raise ValidationError(
                    f"Journal entry is not balanced. Debit: {total_dr}, Credit: {total_cr}"
                )

    @transaction.atomic
    def post(self, posted_by):
        """Post journal entry — moves to POSTED state."""
        self.clean()
        self.status = VoucherStatus.POSTED
        self.approved_by = posted_by
        self.approved_at = timezone.now()
        self.save()


# ── Journal Line (Individual Debit/Credit) ────────────────────
class JournalLine(models.Model):
    """
    Each line of a journal entry — either a debit or credit.
    Exactly one of debit_amount or credit_amount should be non-zero.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    ledger = models.ForeignKey(Ledger, on_delete=models.PROTECT, related_name='journal_lines')

    debit_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    credit_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))

    # For foreign currency transactions
    foreign_currency = models.CharField(max_length=3, blank=True)
    foreign_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    # GST line details
    gst_category = models.CharField(max_length=20, blank=True)  # CGST, SGST, IGST, CESS
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))

    # Cost center / project allocation
    cost_center = models.ForeignKey('CostCenter', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True)

    narration = models.CharField(max_length=500, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'journal_lines'
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['ledger', 'journal']),
            models.Index(fields=['journal']),
        ]

    def __str__(self):
        if self.debit_amount:
            return f"Dr {self.ledger.name} {self.debit_amount}"
        return f"Cr {self.ledger.name} {self.credit_amount}"


# ── Cost Center ───────────────────────────────────────────────
class CostCenter(models.Model):
    """Department or profit center for cost allocation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cost_centers')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_centers')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cost_centers'
        unique_together = ['company', 'name']

    def __str__(self):
        return f"{self.company.name} — {self.name}"


# ── Project ───────────────────────────────────────────────────
class Project(models.Model):
    """Project-wise accounting and cost tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, blank=True)
    client = models.ForeignKey(Ledger, on_delete=models.SET_NULL, null=True, blank=True)
    budget = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='active', choices=[
        ('active', 'Active'), ('completed', 'Completed'), ('on_hold', 'On Hold'), ('cancelled', 'Cancelled')
    ])
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projects'
        unique_together = ['company', 'code']

    def __str__(self):
        return f"{self.name} ({self.company.name})"


# ── Currency Rate ─────────────────────────────────────────────
class CurrencyRate(models.Model):
    """Daily exchange rates for multi-currency transactions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='currency_rates')
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=15, decimal_places=6)
    date = models.DateField(db_index=True)
    source = models.CharField(max_length=50, default='manual')  # manual, api
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'currency_rates'
        unique_together = ['company', 'from_currency', 'to_currency', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"1 {self.from_currency} = {self.rate} {self.to_currency} on {self.date}"
