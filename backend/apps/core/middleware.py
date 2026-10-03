"""
SERENIA ACCOUNTING — core/middleware.py
==========================================
AuditLogMiddleware: records every state-changing request to AuditLog.
CompanyContextMiddleware: resolves X-Company-Id header into request.company
and enforces that the requesting user has access to that company.
"""

import json
from django.utils.deprecation import MiddlewareMixin


class CompanyContextMiddleware(MiddlewareMixin):
    """
    Reads the X-Company-Id header and attaches the resolved Company
    object to request.company. Views use this for data scoping.
    Does NOT raise errors here — individual views validate access
    via apps.core.permissions.CompanyPermission for clearer error messages.
    """

    def process_request(self, request):
        request.company = None
        company_id = request.headers.get('X-Company-Id')
        if not company_id:
            return None

        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return None

        from apps.accounts.models import Company

        try:
            company = Company.objects.get(id=company_id, is_active=True)
        except (Company.DoesNotExist, ValueError, Exception):
            return None

        # Verify access (super admins bypass)
        if request.user.is_super_admin:
            request.company = company
            return None

        has_access = company.user_accesses.filter(user=request.user, is_active=True).exists()
        if has_access:
            request.company = company

        return None


class AuditLogMiddleware(MiddlewareMixin):
    """
    Logs all non-GET requests made by authenticated users.
    Captures the action, model touched (inferred from URL), IP, and user agent.
    Detailed before/after diffs are recorded by individual viewsets
    via apps.core.audit.log_action() for richer context.
    """

    AUDITED_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}

    def process_response(self, request, response):
        if request.method not in self.AUDITED_METHODS:
            return response

        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return response

        # Skip auth endpoints (login/logout/refresh) — no business data changed
        if '/auth/' in request.path:
            return response

        # Only log successful mutations
        if response.status_code >= 400:
            return response

        try:
            from apps.accounts.models import AuditLog

            AuditLog.objects.create(
                user=user,
                company=getattr(request, 'company', None),
                action=f"{request.method.lower()}_{request.path.strip('/').replace('/', '_')}",
                model_name=self._infer_model(request.path),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )
        except Exception:
            # Never let audit logging break the actual request
            pass

        return response

    @staticmethod
    def _infer_model(path: str) -> str:
        parts = [p for p in path.strip('/').split('/') if p]
        # e.g. /api/v1/ledger/ledgers/<id>/ -> "ledger.ledgers"
        if len(parts) >= 3:
            return f"{parts[2]}"
        return 'unknown'

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
