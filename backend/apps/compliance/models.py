"""
SERENIA ACCOUNTING — compliance/models.py
=============================================
Statutory filing calendar, compliance alerts, and
regulatory report tracking (GST, TDS, ROC, Income Tax, etc.)
"""

import uuid
from django.db import models
from apps.accounts.models import Company, User


class ComplianceCategory(models.TextChoices):
    GST = 'gst', 'GST'
    TDS = 'tds', 'TDS / TCS'
    INCOME_TAX = 'income_tax', 'Income Tax'
    ROC = 'roc', 'ROC / Companies Act'
    PF_ESI = 'pf_esi', 'PF / ESI'
    PROFESSIONAL_TAX = 'professional_tax', 'Professional Tax'
    OTHER = 'other', 'Other Statutory'


class FilingFrequency(models.TextChoices):
    MONTHLY = 'monthly', 'Monthly'
    QUARTERLY = 'quarterly', 'Quarterly'
    HALF_YEARLY = 'half_yearly', 'Half Yearly'
    ANNUALLY = 'annually', 'Annually'
    ONE_TIME = 'one_time', 'One Time'


class ComplianceTask(models.Model):
    """A recurring or one-time statutory compliance obligation."""
    STATUS = [('pending', 'Pending'), ('in_progress', 'In Progress'), ('filed', 'Filed'), ('overdue', 'Overdue')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='compliance_tasks')
    category = models.CharField(max_length=20, choices=ComplianceCategory.choices)
    title = models.CharField(max_length=255)          # e.g., "GSTR-3B Filing"
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=15, choices=FilingFrequency.choices, default=FilingFrequency.MONTHLY)

    due_date = models.DateField(db_index=True)
    period_label = models.CharField(max_length=20, blank=True)  # e.g., "March 2025"
    status = models.CharField(max_length=15, choices=STATUS, default='pending')

    reminder_days_before = models.IntegerField(default=3)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_tasks')

    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_compliance_tasks')
    reference_number = models.CharField(max_length=100, blank=True)  # ARN, acknowledgement number etc.
    attachments = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_tasks'
        ordering = ['due_date']
        indexes = [models.Index(fields=['company', 'due_date', 'status'])]

    def __str__(self):
        return f"{self.title} — Due {self.due_date}"
