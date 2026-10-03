"""
SERENIA ACCOUNTING — developer_mode/serializers.py
======================================================
SystemSetting, Theme, NavigationItem, PageContent serializers
and viewsets. All restricted to Super Admins (IsSuperAdmin).
SystemSetting reads are cached in Redis via SystemSetting.get().
"""

from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from apps.developer_mode.models import SystemSetting, Theme, NavigationItem, PageContent
from apps.core.permissions import IsSuperAdmin


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = '__all__'
        read_only_fields = ['id', 'updated_by', 'updated_at', 'created_at']


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class NavigationItemSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = NavigationItem
        fields = '__all__'
        read_only_fields = ['id']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by('sort_order')
        return NavigationItemSerializer(children, many=True).data


class PageContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageContent
        fields = '__all__'
        read_only_fields = ['id', 'updated_by', 'updated_at']


# ── ViewSets (Super Admin only) ────────────────────────────────
class SystemSettingViewSet(viewsets.ModelViewSet):
    serializer_class = SystemSettingSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = SystemSetting.objects.all()
    filterset_fields = ['category']
    lookup_field = 'key'

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
        # Invalidate cache for this setting
        from django.core.cache import cache
        cache.delete(f"sys_setting:{serializer.instance.key}")


class PublicSettingsView(APIView):
    """
    GET /api/v1/developer/public-settings/
    Returns only is_public=True settings — used by the landing page
    and login screen for branding (app name, logo, colors) WITHOUT
    requiring authentication.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        settings_qs = SystemSetting.objects.filter(is_public=True)
        data = {s.key: s.value for s in settings_qs}
        return Response(data)


class ThemeViewSet(viewsets.ModelViewSet):
    serializer_class = ThemeSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = Theme.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def active(self, request):
        """Public endpoint — returns the currently active theme for app-wide styling."""
        from django.core.cache import cache
        cached = cache.get('active_theme')
        if cached:
            return Response(cached)

        theme = Theme.objects.filter(is_active=True).first()
        if not theme:
            theme = Theme.objects.create(name='Default', is_active=True)

        data = ThemeSerializer(theme).data
        cache.set('active_theme', data, 3600)
        return Response(data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        theme = self.get_object()
        theme.is_active = True
        theme.save()  # save() handles deactivating others + cache invalidation
        return Response(ThemeSerializer(theme).data)


class NavigationItemViewSet(viewsets.ModelViewSet):
    serializer_class = NavigationItemSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = NavigationItem.objects.filter(parent__isnull=True).order_by('sort_order')

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public(self, request):
        """Public endpoint for landing page navigation."""
        location = request.query_params.get('location', 'header')
        items = NavigationItem.objects.filter(
            parent__isnull=True, is_active=True
        ).filter(location__in=[location, 'both']).order_by('sort_order')
        return Response(NavigationItemSerializer(items, many=True).data)


class PageContentViewSet(viewsets.ModelViewSet):
    serializer_class = PageContentSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = PageContent.objects.all()
    lookup_field = 'section'

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public(self, request):
        """Public endpoint — all visible page content for the landing page."""
        content = PageContent.objects.filter(is_visible=True)
        return Response(PageContentSerializer(content, many=True).data)
