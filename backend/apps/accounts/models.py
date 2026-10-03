"""
SERENIA ACCOUNTING — accounts/models.py
========================================
Custom User model, Company, Branch, Financial Year,
Role definitions, and User-Company access mapping.

All accounting data is scoped to a Company.
A User can belong to multiple companies with different roles.
"""

import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


# ── Role Constants ────────────────────────────────────────────
class UserRole(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super Administrator'
    ADMIN = 'admin', 'Administrator'
    CA = 'ca', 'Chartered Accountant'
    ACCOUNTANT = 'accountant', 'Accountant'
    AUDITOR = 'auditor', 'Auditor'
    MANAGER = 'manager', 'Manager'
    VIEWER = 'viewer', 'Viewer (Read-Only)'


class CompanyType(models.TextChoices):
    PRIVATE_LIMITED = 'pvt_ltd', 'Private Limited'
    PUBLIC_LIMITED = 'pub_ltd', 'Public Limited'
    PARTNERSHIP = 'partnership', 'Partnership'
    PROPRIETORSHIP = 'proprietorship', 'Proprietorship'
    LLP = 'llp', 'Limited Liability Partnership'
    NGO = 'ngo', 'Non-Governmental Organization'
    TRUST = 'trust', 'Trust'
    OTHER = 'other', 'Other'


# ── User Manager ──────────────────────────────────────────────
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.SUPER_ADMIN)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


# ── User Model ────────────────────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model using email as the primary identifier.
    Supports multi-company access via UserCompanyAccess.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.ACCOUNTANT)
    phone = PhoneNumberField(blank=True, null=True)

    # Professional info
    qualification = models.CharField(max_length=100, blank=True)  # e.g., CA, CPA, ACCA
    membership_number = models.CharField(max_length=50, blank=True)  # ICAI membership

    # Profile
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # Preferences
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    date_format = models.CharField(max_length=20, default='DD/MM/YYYY')
    theme = models.CharField(max_length=20, default='light')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'auth_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN

    @property
    def can_audit(self):
        return self.role in [UserRole.SUPER_ADMIN, UserRole.CA, UserRole.AUDITOR]


# ── Company ───────────────────────────────────────────────────
class Company(models.Model):
    """
    Represents a business entity. All financial data is scoped here.
    A platform can host unlimited companies.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    legal_name = models.CharField(max_length=255, blank=True)
    company_type = models.CharField(max_length=20, choices=CompanyType.choices, default=CompanyType.PRIVATE_LIMITED)

    # Identity numbers
    gstin = models.CharField(max_length=15, blank=True, db_index=True)  # GST Number
    pan = models.CharField(max_length=10, blank=True)
    tan = models.CharField(max_length=10, blank=True)
    cin = models.CharField(max_length=21, blank=True)  # Company Identification Number

    # Contact
    email = models.EmailField(blank=True)
    phone = PhoneNumberField(blank=True, null=True)
    website = models.URLField(blank=True)

    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    state_code = models.CharField(max_length=5, blank=True)  # GST state code
    pincode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='India')

    # Branding
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)

    # Financial settings
    currency = models.CharField(max_length=3, default='INR')
    fiscal_year_start = models.IntegerField(default=4)  # April = 4
    accounting_method = models.CharField(max_length=20, default='accrual', choices=[
        ('accrual', 'Accrual'), ('cash', 'Cash')
    ])

    # Status
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_companies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def current_financial_year(self):
        from django.utils import timezone
        now = timezone.now()
        year = now.year
        if now.month < self.fiscal_year_start:
            year -= 1
        return self.financial_years.filter(start_date__year=year).first()


# ── Branch ────────────────────────────────────────────────────
class Branch(models.Model):
    """Sub-unit of a Company. Used for branch-wise accounting."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    gstin = models.CharField(max_length=15, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    is_head_office = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'branches'
        unique_together = ['company', 'code']
        verbose_name_plural = 'Branches'

    def __str__(self):
        return f"{self.company.name} — {self.name}"


# ── Financial Year ────────────────────────────────────────────
class FinancialYear(models.Model):
    """
    Represents one accounting period (April to March for Indian companies).
    All transactions are tagged to a financial year.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='financial_years')
    label = models.CharField(max_length=20)       # e.g., "FY 2024-25"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'financial_years'
        unique_together = ['company', 'label']
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.company.name} — {self.label}"


# ── User Company Access ───────────────────────────────────────
class UserCompanyAccess(models.Model):
    """
    Maps users to companies with specific roles.
    One user can have different roles in different companies.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_accesses')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='user_accesses')
    role = models.CharField(max_length=20, choices=UserRole.choices)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)

    # Granular permissions (JSON field)
    permissions = models.JSONField(default=dict)

    is_active = models.BooleanField(default=True)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_accesses')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_company_access'
        unique_together = ['user', 'company']

    def __str__(self):
        return f"{self.user.email} → {self.company.name} ({self.role})"


# ── Audit Log ─────────────────────────────────────────────────
class AuditLog(models.Model):
    """
    Immutable audit trail for all actions performed in the system.
    Captures who did what, when, on which company's data.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)       # e.g., "created_voucher"
    model_name = models.CharField(max_length=100)   # e.g., "PaymentVoucher"
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict)         # Before/after diff
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user} — {self.action} at {self.timestamp}"
