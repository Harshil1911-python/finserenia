"""
SERENIA ACCOUNTING — developer_mode/urls.py
==============================================
Routes for /api/v1/developer/
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from apps.developer_mode.serializers import (
    SystemSettingViewSet, ThemeViewSet, NavigationItemViewSet, PageContentViewSet,
    PublicSettingsView,
)

router = DefaultRouter()
router.register(r'settings', SystemSettingViewSet, basename='system-setting')
router.register(r'theme', ThemeViewSet, basename='theme')
router.register(r'navigation', NavigationItemViewSet, basename='navigation-item')
router.register(r'content', PageContentViewSet, basename='page-content')

urlpatterns = [
    path('public-settings/', PublicSettingsView.as_view(), name='public-settings'),
] + router.urls
