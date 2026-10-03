"""
SERENIA ACCOUNTING — accounts/views_users.py
===============================================
User listing/management — restricted to Admins and Super Admins.
"""

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.accounts.models import User, UserRole
from apps.accounts.serializers import UserSerializer, UserCreateSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    List/create/manage platform users.
    - Super Admins see all users.
    - Admins see only users with access to their active company.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return User.objects.all().order_by('first_name')

        company = getattr(self.request, 'company', None)
        if not company:
            return User.objects.filter(id=user.id)

        if user.role not in [UserRole.ADMIN, UserRole.CA]:
            return User.objects.filter(id=user.id)

        user_ids = company.user_accesses.filter(is_active=True).values_list('user_id', flat=True)
        return User.objects.filter(id__in=user_ids).order_by('first_name')

    def create(self, request, *args, **kwargs):
        if not (request.user.is_super_admin or request.user.role in [UserRole.ADMIN, UserRole.CA]):
            return Response({'error': 'Insufficient permissions to create users.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)
