"""
SERENIA ACCOUNTING — banking/models.py
==========================================
Bank reconciliation records — matching statement lines
against ledger journal entries.
"""

import uuid
from decimal import Decimal
from django.db import models
from apps.accounts.models import Company, User
from apps.ledger.models import Ledger, JournalLine


class BankStatementImport(models.Model):
    """Tracks a single bank statement upload/import batch."""
    STATUS = [('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_imports')
    bank_ledger = models.ForeignKey(Ledger, on_delete=models.CASCADE, related_name='statement_imports')
    file_name = models.CharField(max_length=255)
    statement_from = models.DateField()
    statement_to = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS, default='processing')
    total_records = models.IntegerField(default=0)
    matched_records = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bank_statement_imports'


class BankStatementLine(models.Model):
    """Individual transaction line from an imported bank statement."""
    MATCH_STATUS = [
        ('unmatched', 'Unmatched'), ('matched', 'Matched'),
        ('suggested', 'Suggested Match'), ('ignored', 'Ignored'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    statement_import = models.ForeignKey(BankStatementImport, on_delete=models.CASCADE, related_name='lines')
    date = models.DateField()
    description = models.CharField(max_length=500)
    reference = models.CharField(max_length=100, blank=True)
    debit = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    credit = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    balance = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    match_status = models.CharField(max_length=10, choices=MATCH_STATUS, default='unmatched')
    matched_journal_line = models.ForeignKey(JournalLine, on_delete=models.SET_NULL, null=True, blank=True, related_name='bank_matches')
    matched_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    matched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'bank_statement_lines'
        indexes = [models.Index(fields=['statement_import', 'match_status'])]
