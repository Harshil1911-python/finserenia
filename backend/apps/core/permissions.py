"""
SERENIA ACCOUNTING — core/permissions.py
===========================================
Role-based and company-scoped permission classes for DRF views.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class CompanyPermission(BasePermission):
    """
    Ensures the request includes a valid X-Company-Id header
    and the user has active access to that company.
    Super admins bypass this check.
    """
    message = 'You do not have access to this company.'

    def has_permission(self, request, view):
        if request.user.is_super_admin:
            return True
        return getattr(request, 'company', None) is not None


class ReadOnlyPermission(BasePermission):
    """Allows GET/HEAD/OPTIONS for any authenticated user; write requires elevated role."""

    WRITE_ROLES = {'super_admin', 'admin', 'ca', 'accountant'}

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in self.WRITE_ROLES


class IsSuperAdmin(BasePermission):
    """Restricts access to Super Administrators only (Developer Mode)."""
    message = 'Only Super Administrators can access this resource.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_super_admin


class CanApproveVouchers(BasePermission):
    """Roles allowed to approve/reject journal entries and vouchers."""

    APPROVER_ROLES = {'super_admin', 'admin', 'ca', 'manager'}

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.APPROVER_ROLES


class CanAccessAuditModule(BasePermission):
    """Restricts audit module access to CA / Auditor / Admin / Super Admin."""

    AUDIT_ROLES = {'super_admin', 'admin', 'ca', 'auditor'}

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.AUDIT_ROLES


class IsReadOnlyOrViewerSafe(BasePermission):
    """Viewers can only read; all other authenticated roles have full access within company scope."""

    def has_permission(self, request, view):
        if request.user.role == 'viewer':
            return request.method in SAFE_METHODS
        return True
