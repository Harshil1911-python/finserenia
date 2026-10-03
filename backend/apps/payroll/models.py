"""
SERENIA ACCOUNTING — payroll/models.py
=======================================
Employee management, salary structures, payroll runs,
payslips, attendance, and statutory deductions (PF/ESI/PT).
"""

import uuid
from decimal import Decimal
from django.db import models
from apps.accounts.models import Company, User, FinancialYear


class Employee(models.Model):
    EMPLOYMENT_TYPE = [('full_time', 'Full Time'), ('part_time', 'Part Time'), ('contract', 'Contract'), ('intern', 'Intern')]
    GENDER = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    employee_code = models.CharField(max_length=20, db_index=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Personal
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER)
    pan = models.CharField(max_length=10, blank=True)
    aadhar = models.CharField(max_length=12, blank=True)

    # Employment
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=15, choices=EMPLOYMENT_TYPE, default='full_time')
    joining_date = models.DateField()
    leaving_date = models.DateField(null=True, blank=True)

    # Salary
    salary_structure = models.ForeignKey('SalaryStructure', on_delete=models.SET_NULL, null=True, blank=True)
    bank_account = models.CharField(max_length=30, blank=True)
    bank_ifsc = models.CharField(max_length=11, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)

    # Statutory
    pf_number = models.CharField(max_length=30, blank=True)
    esi_number = models.CharField(max_length=30, blank=True)
    uan_number = models.CharField(max_length=12, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'employees'
        unique_together = ['company', 'employee_code']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_code})"


class SalaryStructure(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='salary_structures')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Earnings
    basic_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50'))  # % of CTC
    hra_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20'))
    special_allowance_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20'))
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    medical_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))

    # Deductions
    pf_applicable = models.BooleanField(default=True)
    esi_applicable = models.BooleanField(default=True)
    professional_tax_applicable = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'salary_structures'

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class PayrollRun(models.Model):
    STATUS = [('draft', 'Draft'), ('processing', 'Processing'), ('completed', 'Completed'), ('cancelled', 'Cancelled')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payroll_runs')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.PROTECT)
    month = models.IntegerField()
    year = models.IntegerField()
    status = models.CharField(max_length=15, choices=STATUS, default='draft')
    total_gross = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    total_deductions = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    total_net = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    journal_entry = models.OneToOneField('ledger.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payroll_runs'
        unique_together = ['company', 'month', 'year']


class Payslip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='payslips')

    # Working days
    total_working_days = models.IntegerField(default=26)
    days_worked = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('26'))
    days_absent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    days_leave = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))

    # Earnings
    basic = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    hra = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    other_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    # Deductions
    pf_employee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    pf_employer = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    esi_employee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    esi_employer = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    professional_tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    tds = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payslips'
        unique_together = ['payroll_run', 'employee']
