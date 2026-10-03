"""
SERENIA ACCOUNTING — accounts/views_auth.py
==============================================
JWT authentication endpoints: login, logout (token blacklist),
token refresh, current user (me), change password.
Rate-limited via django-axes (account lockout protection).
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone

from apps.accounts.models import User, AuditLog
from apps.accounts.serializers import (
    LoginSerializer, UserSerializer, ChangePasswordSerializer,
)


class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Body: { email, password }
    Returns: { tokens: { access, refresh }, user: {...} }

    Brute-force protection via django-axes: after 5 failed attempts
    within 30 minutes, the account+IP combination is locked out.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        tokens = serializer.create_tokens(user)

        # Reset failed login counter on success
        user.failed_login_attempts = 0
        user.last_login_ip = self._get_client_ip(request)
        user.last_login = timezone.now()
        user.save(update_fields=['failed_login_attempts', 'last_login_ip', 'last_login'])

        AuditLog.objects.create(
            user=user, action='login', model_name='User', object_id=str(user.id),
            object_repr=user.email, ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )

        return Response({
            'tokens': tokens,
            'user': UserSerializer(user).data,
        })

    @staticmethod
    def _get_client_ip(request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Body: { refresh }
    Blacklists the refresh token so it can no longer be used.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass  # Already invalid/expired — fine for logout

        AuditLog.objects.create(
            user=request.user, action='logout', model_name='User',
            object_id=str(request.user.id), object_repr=request.user.email,
        )

        return Response({'detail': 'Logged out successfully'})


class MeView(APIView):
    """
    GET    /api/v1/auth/me/  — current user profile + company accesses
    PATCH  /api/v1/auth/me/  — update own profile fields
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        allowed_fields = {
            'first_name', 'last_name', 'phone', 'qualification',
            'membership_number', 'bio', 'timezone', 'date_format', 'theme',
        }
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        serializer = UserSerializer(request.user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/
    Body: { current_password, new_password, confirm_password }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        AuditLog.objects.create(
            user=user, action='change_password', model_name='User',
            object_id=str(user.id), object_repr=user.email,
        )

        return Response({'detail': 'Password updated successfully'})
