"""
SERENIA ACCOUNTING — audit/models.py
========================================
Audit planning, working papers, compliance checklists,
risk assessment, observation tracking, audit reporting.
"""

import uuid
from django.db import models
from apps.accounts.models import Company, User, FinancialYear


class AuditPlan(models.Model):
    STATUS = [('planning', 'Planning'), ('in_progress', 'In Progress'), ('review', 'Under Review'), ('completed', 'Completed')]
    AUDIT_TYPES = [
        ('statutory', 'Statutory Audit'), ('internal', 'Internal Audit'),
        ('tax', 'Tax Audit'), ('gst', 'GST Audit'), ('stock', 'Stock Audit'), ('special', 'Special Purpose Audit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='audit_plans')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name='audit_plans')
    title = models.CharField(max_length=255)
    audit_type = models.CharField(max_length=15, choices=AUDIT_TYPES, default='statutory')
    status = models.CharField(max_length=15, choices=STATUS, default='planning')

    lead_auditor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='led_audits')
    team_members = models.ManyToManyField(User, blank=True, related_name='audit_assignments')

    scope = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    materiality_threshold = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    planned_start_date = models.DateField()
    planned_end_date = models.DateField()
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_audit_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'audit_plans'
        ordering = ['-planned_start_date']

    def __str__(self):
        return f"{self.title} — {self.company.name} ({self.financial_year.label})"


class RiskAssessment(models.Model):
    RISK_LEVELS = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit_plan = models.ForeignKey(AuditPlan, on_delete=models.CASCADE, related_name='risk_assessments')
    area = models.CharField(max_length=255)  # e.g., "Revenue Recognition"
    description = models.TextField(blank=True)
    inherent_risk = models.CharField(max_length=10, choices=RISK_LEVELS, default='medium')
    control_risk = models.CharField(max_length=10, choices=RISK_LEVELS, default='medium')
    overall_risk = models.CharField(max_length=10, choices=RISK_LEVELS, default='medium')
    audit_response = models.TextField(blank=True)  # Planned audit procedures
    assessed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_risk_assessments'


class WorkingPaper(models.Model):
    STATUS = [('draft', 'Draft'), ('reviewed', 'Reviewed'), ('finalized', 'Finalized')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit_plan = models.ForeignKey(AuditPlan, on_delete=models.CASCADE, related_name='working_papers')
    reference_number = models.CharField(max_length=50)  # e.g., "WP-101"
    title = models.CharField(max_length=255)
    section = models.CharField(max_length=100, blank=True)  # e.g., "Cash & Bank", "Revenue"
    procedures_performed = models.TextField(blank=True)
    conclusions = models.TextField(blank=True)
    attachments = models.JSONField(default=list)

    status = models.CharField(max_length=15, choices=STATUS, default='draft')
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='prepared_working_papers')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_working_papers')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'audit_working_papers'
        unique_together = ['audit_plan', 'reference_number']
        ordering = ['reference_number']


class ComplianceChecklistItem(models.Model):
    STATUS = [('pending', 'Pending'), ('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant'), ('not_applicable', 'Not Applicable')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit_plan = models.ForeignKey(AuditPlan, on_delete=models.CASCADE, related_name='checklist_items')
    category = models.CharField(max_length=100)  # e.g., "Companies Act", "GST", "Income Tax"
    requirement = models.TextField()
    reference_section = models.CharField(max_length=100, blank=True)  # Legal section reference
    status = models.CharField(max_length=15, choices=STATUS, default='pending')
    remarks = models.TextField(blank=True)
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'audit_compliance_checklist'


class AuditObservation(models.Model):
    SEVERITY = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')]
    STATUS = [('open', 'Open'), ('management_response', 'Management Response Received'), ('resolved', 'Resolved'), ('closed', 'Closed')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit_plan = models.ForeignKey(AuditPlan, on_delete=models.CASCADE, related_name='observations')
    working_paper = models.ForeignKey(WorkingPaper, on_delete=models.SET_NULL, null=True, blank=True, related_name='observations')

    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY, default='medium')
    financial_impact = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    recommendation = models.TextField(blank=True)
    management_response = models.TextField(blank=True)

    status = models.CharField(max_length=25, choices=STATUS, default='open')
    raised_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='raised_observations')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_observations')
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'audit_observations'
        ordering = ['-severity', '-created_at']
