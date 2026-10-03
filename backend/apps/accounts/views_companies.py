"""
SERENIA ACCOUNTING — accounts/views_companies.py
===================================================
Company, Branch, Financial Year management.
Users see only companies they have UserCompanyAccess to
(unless they are Super Admin, who sees all).
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from apps.accounts.models import Company, Branch, FinancialYear, UserCompanyAccess, UserRole, AuditLog
from apps.accounts.serializers import (
    CompanySerializer, CompanyListSerializer, BranchSerializer,
    FinancialYearSerializer, GrantAccessSerializer, UserCompanyAccessSerializer,
)
from apps.core.permissions import IsSuperAdmin


class CompanyViewSet(viewsets.ModelViewSet):
    """
    CRUD for companies. List is scoped to the user's accessible companies.
    Creating a company automatically:
    - Grants the creator 'admin' access
    - Creates a default financial year (April–March)
    - Sets up the standard Chart of Accounts template
    """
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return CompanyListSerializer
        return CompanySerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Company.objects.all().prefetch_related('branches', 'financial_years')
        company_ids = user.company_accesses.filter(is_active=True).values_list('company_id', flat=True)
        return Company.objects.filter(id__in=company_ids, is_active=True).prefetch_related('branches', 'financial_years')

    @transaction.atomic
    def perform_create(self, serializer):
        company = serializer.save(created_by=self.request.user)

        # Grant creator admin access
        UserCompanyAccess.objects.create(
            user=self.request.user, company=company, role=UserRole.ADMIN,
            granted_by=self.request.user,
        )

        # Create head office branch
        Branch.objects.create(
            company=company, name='Head Office', code='HO',
            gstin=company.gstin, city=company.city, state=company.state,
            is_head_office=True,
        )

        # Create current financial year (April-March, Indian standard)
        from datetime import date
        today = date.today()
        if today.month >= company.fiscal_year_start:
            start = date(today.year, company.fiscal_year_start, 1)
            end = date(today.year + 1, company.fiscal_year_start - 1 or 12, 1)
        else:
            start = date(today.year - 1, company.fiscal_year_start, 1)
            end = date(today.year, company.fiscal_year_start - 1 or 12, 1)

        from calendar import monthrange
        end = end.replace(day=monthrange(end.year, end.month)[1])

        FinancialYear.objects.create(
            company=company,
            label=f"FY {start.year}-{str(end.year)[2:]}",
            start_date=start, end_date=end, is_current=True,
        )

        # Bootstrap standard chart of accounts
        from apps.ledger.bootstrap import create_standard_chart_of_accounts
        create_standard_chart_of_accounts(company)

        AuditLog.objects.create(
            user=self.request.user, company=company, action='create_company',
            model_name='Company', object_id=str(company.id), object_repr=company.name,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def grant_access(self, request, pk=None):
        """Grant another user access to this company with a specific role."""
        company = self.get_object()

        # Only admins/super admins of this company can grant access
        requester_access = company.user_accesses.filter(user=request.user, is_active=True).first()
        if not request.user.is_super_admin and (not requester_access or requester_access.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]):
            return Response({'error': 'Only company administrators can grant access.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = GrantAccessSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from apps.accounts.models import User
        try:
            target_user = User.objects.get(id=serializer.validated_data['user_id'])
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        access, created = UserCompanyAccess.objects.update_or_create(
            user=target_user, company=company,
            defaults={
                'role': serializer.validated_data['role'],
                'branch_id': serializer.validated_data.get('branch_id'),
                'permissions': serializer.validated_data.get('permissions', {}),
                'is_active': True,
                'granted_by': request.user,
            },
        )

        AuditLog.objects.create(
            user=request.user, company=company, action='grant_access',
            model_name='UserCompanyAccess', object_id=str(access.id),
            object_repr=f"{target_user.email} -> {access.role}",
        )

        return Response(UserCompanyAccessSerializer(access).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """List all users with access to this company."""
        company = self.get_object()
        accesses = company.user_accesses.filter(is_active=True).select_related('user', 'branch')
        from apps.accounts.serializers import UserSerializer
        data = [{
            'access_id': str(a.id),
            'user': UserSerializer(a.user).data,
            'role': a.role,
            'branch': a.branch.name if a.branch else None,
        } for a in accesses]
        return Response(data)


class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        company_id = self.request.headers.get('X-Company-Id')
        return Branch.objects.filter(company_id=company_id) if company_id else Branch.objects.none()

    def perform_create(self, serializer):
        company_id = self.request.headers.get('X-Company-Id')
        serializer.save(company_id=company_id)


class FinancialYearViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialYearSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        company_id = self.request.headers.get('X-Company-Id')
        return FinancialYear.objects.filter(company_id=company_id) if company_id else FinancialYear.objects.none()

    def perform_create(self, serializer):
        company_id = self.request.headers.get('X-Company-Id')
        serializer.save(company_id=company_id)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a financial year — prevents further postings."""
        fy = self.get_object()
        from django.utils import timezone
        fy.is_closed = True
        fy.closed_at = timezone.now()
        fy.closed_by = request.user
        fy.save()

        AuditLog.objects.create(
            user=request.user, company=fy.company, action='close_financial_year',
            model_name='FinancialYear', object_id=str(fy.id), object_repr=fy.label,
        )
        return Response(FinancialYearSerializer(fy).data)
