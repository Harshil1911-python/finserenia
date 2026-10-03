"""
SERENIA ACCOUNTING — developer_mode/models.py
===============================================
Super Admin-only panel for branding, theme, feature toggles,
SMTP config, content management, and system settings.
Settings stored as key-value pairs in DB, cached in Redis.
"""

import uuid
from django.db import models
from apps.accounts.models import User


class SystemSetting(models.Model):
    """
    Key-value store for all developer-mode configurations.
    Category groups related settings together.
    Cached in Redis on first access.
    """
    CATEGORIES = [
        ('branding', 'Branding'),
        ('theme', 'Theme & Colors'),
        ('features', 'Feature Flags'),
        ('smtp', 'Email / SMTP'),
        ('security', 'Security'),
        ('storage', 'Storage'),
        ('api', 'API Settings'),
        ('content', 'Content Management'),
        ('landing', 'Landing Page'),
        ('navigation', 'Navigation'),
        ('seo', 'SEO & Meta'),
        ('integrations', 'Integrations'),
    ]
    VALUE_TYPES = [
        ('string', 'String'), ('boolean', 'Boolean'), ('integer', 'Integer'),
        ('json', 'JSON'), ('color', 'Color'), ('image', 'Image URL'),
        ('email', 'Email'), ('url', 'URL'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=30, choices=CATEGORIES, db_index=True)
    key = models.CharField(max_length=100, unique=True, db_index=True)
    label = models.CharField(max_length=200)         # Human-readable label
    value = models.TextField(default='')              # Serialized value
    value_type = models.CharField(max_length=10, choices=VALUE_TYPES, default='string')
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)   # Can non-admins read this?
    is_required = models.BooleanField(default=False)
    default_value = models.TextField(default='')

    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'system_settings'
        ordering = ['category', 'key']

    def __str__(self):
        return f"{self.category}.{self.key} = {self.value[:50]}"

    @classmethod
    def get(cls, key, default=None):
        """Get a setting value, checking Redis cache first."""
        from django.core.cache import cache
        cache_key = f"sys_setting:{key}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            setting = cls.objects.get(key=key)
            cache.set(cache_key, setting.value, 3600)
            return setting.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value, updated_by=None):
        """Update a setting and invalidate its cache."""
        from django.core.cache import cache
        setting, _ = cls.objects.get_or_create(key=key)
        setting.value = str(value)
        setting.updated_by = updated_by
        setting.save()
        cache.delete(f"sys_setting:{key}")
        return setting


# ── Theme Customization ────────────────────────────────────────
class Theme(models.Model):
    """Saved theme profiles. Active theme is applied app-wide."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    mode = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System')], default='light')

    # Typography
    font_family_heading = models.CharField(max_length=100, default='Inter')
    font_family_body = models.CharField(max_length=100, default='Inter')
    font_size_base = models.IntegerField(default=14)

    # Colors
    color_primary = models.CharField(max_length=7, default='#6C5CE7')
    color_primary_light = models.CharField(max_length=7, default='#A29BFE')
    color_secondary = models.CharField(max_length=7, default='#00B894')
    color_accent = models.CharField(max_length=7, default='#FDCB6E')
    color_danger = models.CharField(max_length=7, default='#D63031')
    color_warning = models.CharField(max_length=7, default='#FDCB6E')
    color_success = models.CharField(max_length=7, default='#00B894')

    # Light mode surfaces
    color_bg = models.CharField(max_length=7, default='#F8F9FA')
    color_surface = models.CharField(max_length=7, default='#FFFFFF')
    color_border = models.CharField(max_length=7, default='#E9ECEF')
    color_text = models.CharField(max_length=7, default='#2D3436')
    color_text_muted = models.CharField(max_length=7, default='#636E72')

    # Dark mode surfaces
    color_dark_bg = models.CharField(max_length=7, default='#0F1117')
    color_dark_surface = models.CharField(max_length=7, default='#1A1D24')
    color_dark_border = models.CharField(max_length=7, default='#2D2F36')
    color_dark_text = models.CharField(max_length=7, default='#E8EAF0')

    # Border radius
    border_radius_sm = models.CharField(max_length=10, default='6px')
    border_radius_md = models.CharField(max_length=10, default='10px')
    border_radius_lg = models.CharField(max_length=10, default='16px')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'themes'

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"

    def save(self, *args, **kwargs):
        # Only one active theme at a time
        if self.is_active:
            Theme.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
        # Invalidate theme cache
        from django.core.cache import cache
        cache.delete('active_theme')


# ── Navigation Menu ────────────────────────────────────────────
class NavigationItem(models.Model):
    """Customizable navigation menu items for landing page."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=100)
    url = models.CharField(max_length=255)
    target = models.CharField(max_length=10, default='_self', choices=[('_self', 'Same Tab'), ('_blank', 'New Tab')])
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    location = models.CharField(max_length=20, choices=[('header', 'Header'), ('footer', 'Footer'), ('both', 'Both')], default='header')
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'navigation_items'
        ordering = ['sort_order']


# ── Page Content ───────────────────────────────────────────────
class PageContent(models.Model):
    """CMS for marketing page content (hero, features, pricing, etc.)."""
    SECTIONS = [
        ('hero', 'Hero Section'), ('features', 'Features'), ('pricing', 'Pricing'),
        ('testimonials', 'Testimonials'), ('cta', 'Call to Action'),
        ('about', 'About'), ('contact', 'Contact'), ('footer', 'Footer'),
        ('faq', 'FAQ'), ('announcement', 'Announcement Banner'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.CharField(max_length=30, choices=SECTIONS, unique=True)
    title = models.CharField(max_length=255, blank=True)
    subtitle = models.TextField(blank=True)
    body = models.JSONField(default=dict)   # Rich structured content
    cta_text = models.CharField(max_length=100, blank=True)
    cta_url = models.CharField(max_length=255, blank=True)
    image_url = models.URLField(blank=True)
    is_visible = models.BooleanField(default=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'page_content'

    def __str__(self):
        return f"Content: {self.section}"
