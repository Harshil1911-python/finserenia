"""
SERENIA ACCOUNTING — taxation/models.py
=========================================
GST Master, GSTR-1, GSTR-3B, TDS, TCS models.
Supports Indian taxation system (GST + TDS + TCS).
"""

import uuid
from decimal import Decimal
from django.db import models
from apps.accounts.models import Company, User, FinancialYear
from apps.ledger.models import Ledger, JournalEntry


class GSTRegistrationType(models.TextChoices):
    REGULAR = 'regular', 'Regular'
    COMPOSITION = 'composition', 'Composition'
    UNREGISTERED = 'unregistered', 'Unregistered'
    CONSUMER = 'consumer', 'Consumer'
    SEZ = 'sez', 'SEZ'
    OVERSEAS = 'overseas', 'Overseas'


class SupplyType(models.TextChoices):
    B2B = 'b2b', 'B2B (Business to Business)'
    B2C_LARGE = 'b2cl', 'B2CL (Large B2C)'
    B2C_SMALL = 'b2cs', 'B2CS (Small B2C)'
    EXPORTS = 'exports', 'Exports'
    NIL_RATED = 'nil', 'Nil Rated / Exempt'
    CDN = 'cdn', 'Credit / Debit Notes'


class TDSSection(models.TextChoices):
    SEC_194C = '194C', '194C — Contractors'
    SEC_194J = '194J', '194J — Professional Services'
    SEC_194I = '194I', '194I — Rent'
    SEC_194A = '194A', '194A — Interest'
    SEC_194H = '194H', '194H — Commission'
    SEC_194D = '194D', '194D — Insurance Commission'
    SEC_194B = '194B', '194B — Lottery Winnings'
    SEC_195 = '195', '195 — Non-Resident Payments'


# ── GST Transaction Line ───────────────────────────────────────
class GSTTransaction(models.Model):
    """
    GST detail for each taxable transaction.
    Linked to a JournalEntry.
    Populates GSTR-1 and GSTR-3B.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gst_transactions')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.PROTECT)
    journal = models.OneToOneField(JournalEntry, on_delete=models.CASCADE, related_name='gst_transaction')

    # Counterparty
    party_gstin = models.CharField(max_length=15, blank=True)
    party_name = models.CharField(max_length=255, blank=True)
    party_state_code = models.CharField(max_length=5, blank=True)
    registration_type = models.CharField(max_length=20, choices=GSTRegistrationType.choices, default=GSTRegistrationType.REGULAR)

    # Transaction type
    supply_type = models.CharField(max_length=10, choices=SupplyType.choices, default=SupplyType.B2B)
    is_reverse_charge = models.BooleanField(default=False)
    is_export = models.BooleanField(default=False)
    export_type = models.CharField(max_length=20, blank=True)  # WPAY, WOPAY

    # Invoice details
    invoice_number = models.CharField(max_length=50, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    invoice_value = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))

    # HSN/SAC
    hsn_sac_code = models.CharField(max_length=10, blank=True)
    description = models.CharField(max_length=255, blank=True)

    # Tax amounts
    taxable_value = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    igst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    igst_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    cgst_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    sgst_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    cess_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    cess_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))

    total_tax = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))

    # ITC eligibility
    is_itc_eligible = models.BooleanField(default=True)
    itc_type = models.CharField(max_length=30, blank=True)  # Inputs, Capital goods, etc.

    # GSTR filing
    gstr1_period = models.CharField(max_length=7, blank=True)   # MMYYYY
    gstr1_filed = models.BooleanField(default=False)
    gstr3b_period = models.CharField(max_length=7, blank=True)
    gstr3b_filed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gst_transactions'
        indexes = [
            models.Index(fields=['company', 'invoice_date']),
            models.Index(fields=['party_gstin']),
            models.Index(fields=['gstr1_period']),
        ]

    def save(self, *args, **kwargs):
        self.total_tax = self.igst_amount + self.cgst_amount + self.sgst_amount + self.cess_amount
        super().save(*args, **kwargs)


# ── GSTR Filing ───────────────────────────────────────────────
class GSTRFiling(models.Model):
    """Tracks GSTR-1, GSTR-3B and other return filings."""
    RETURN_TYPES = [
        ('gstr1', 'GSTR-1'), ('gstr2a', 'GSTR-2A'), ('gstr3b', 'GSTR-3B'),
        ('gstr9', 'GSTR-9 Annual'), ('gstr9c', 'GSTR-9C Reconciliation'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'), ('ready', 'Ready to File'), ('filed', 'Filed'), ('error', 'Error')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gstr_filings')
    return_type = models.CharField(max_length=10, choices=RETURN_TYPES)
    period = models.CharField(max_length=7)   # MMYYYY e.g., 032025
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    arn_number = models.CharField(max_length=50, blank=True)   # Acknowledgement number
    filing_date = models.DateTimeField(null=True, blank=True)
    summary_data = models.JSONField(default=dict)
    filed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gstr_filings'
        unique_together = ['company', 'return_type', 'period']


# ── TDS Transaction ───────────────────────────────────────────
class TDSTransaction(models.Model):
    """Tax Deducted at Source record."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tds_transactions')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.PROTECT)
    journal = models.OneToOneField(JournalEntry, on_delete=models.CASCADE, related_name='tds_transaction', null=True, blank=True)

    # Deductee
    deductee_ledger = models.ForeignKey(Ledger, on_delete=models.PROTECT, related_name='tds_as_deductee')
    deductee_pan = models.CharField(max_length=10)
    deductee_name = models.CharField(max_length=255)

    # TDS Details
    section = models.CharField(max_length=10, choices=TDSSection.choices)
    payment_nature = models.CharField(max_length=100, blank=True)
    transaction_date = models.DateField()
    payment_amount = models.DecimalField(max_digits=20, decimal_places=2)
    tds_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tds_amount = models.DecimalField(max_digits=20, decimal_places=2)
    surcharge = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    education_cess = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    total_tax_deducted = models.DecimalField(max_digits=20, decimal_places=2)

    # Deposit
    challan_number = models.CharField(max_length=50, blank=True)
    challan_date = models.DateField(null=True, blank=True)
    bsr_code = models.CharField(max_length=10, blank=True)
    is_deposited = models.BooleanField(default=False)

    # Certificate
    certificate_number = models.CharField(max_length=50, blank=True)
    form_16_issued = models.BooleanField(default=False)

    # TDS Return
    tds_return_period = models.CharField(max_length=10, blank=True)
    tds_return_filed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tds_transactions'
        indexes = [
            models.Index(fields=['company', 'transaction_date']),
            models.Index(fields=['deductee_pan']),
            models.Index(fields=['section']),
        ]

    def save(self, *args, **kwargs):
        self.total_tax_deducted = self.tds_amount + self.surcharge + self.education_cess
        super().save(*args, **kwargs)
