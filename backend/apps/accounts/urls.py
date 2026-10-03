"""
SERENIA ACCOUNTING — accounts/urls.py
========================================
All accounts routes: auth, companies, users.
Consolidated from urls/ subfolder to reduce file count.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views_auth import LoginView, LogoutView, MeView, ChangePasswordView
from apps.accounts.views_companies import CompanyViewSet, BranchViewSet, FinancialYearViewSet
from apps.accounts.views_users import UserViewSet

# Auth routes
auth_urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
]

# Company routes
company_router = DefaultRouter()
company_router.register(r'', CompanyViewSet, basename='company')
company_router.register(r'branches', BranchViewSet, basename='branch')
company_router.register(r'financial-years', FinancialYearViewSet, basename='financial-year')

# User routes
user_router = DefaultRouter()
user_router.register(r'', UserViewSet, basename='user')
