"""
SERENIA ACCOUNTING — core/management/commands/seed_initial_data.py
======================================================================
Idempotent seed command run on every deploy (see docker-compose.yml
and render.yaml startCommand). Creates:
  - Super Admin user (from SUPERADMIN_EMAIL / SUPERADMIN_PASSWORD env)
  - Default system settings (branding, theme, feature flags)
  - Default active theme

Safe to run repeatedly — uses get_or_create throughout.
"""

from django.core.management.base import BaseCommand
from django.conf import settings as django_settings


class Command(BaseCommand):
    help = 'Seeds initial Super Admin user, system settings, and default theme.'

    def handle(self, *args, **options):
        self.create_superadmin()
        self.create_default_settings()
        self.create_default_theme()
        self.stdout.write(self.style.SUCCESS('✓ Initial data seeding complete.'))

    def create_superadmin(self):
        from apps.accounts.models import User, UserRole
        from decouple import config

        email = config('SUPERADMIN_EMAIL', default='superadmin@serenia.app')
        password = config('SUPERADMIN_PASSWORD', default='Serenia@2024')
        name = config('SUPERADMIN_NAME', default='Super Administrator')

        if User.objects.filter(email=email).exists():
            self.stdout.write(f'  Super Admin {email} already exists — skipping.')
            return

        parts = name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

        User.objects.create_superuser(
            email=email, password=password,
            first_name=first_name, last_name=last_name,
            role=UserRole.SUPER_ADMIN,
        )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created Super Admin: {email}'))

    def create_default_settings(self):
        from apps.developer_mode.models import SystemSetting

        defaults = [
            # Branding
            ('branding', 'app_name', 'Application Name', 'Serenia Accounting', 'string', True),
            ('branding', 'app_tagline', 'Tagline', 'Smart Cloud ERP for Modern Businesses', 'string', True),
            ('branding', 'logo_url', 'Logo URL', '', 'image', True),
            ('branding', 'favicon_url', 'Favicon URL', '', 'image', True),
            ('branding', 'support_email', 'Support Email', 'support@serenia.app', 'email', True),

            # Feature flags
            ('features', 'enable_audit_module', 'Audit Module', 'true', 'boolean', False),
            ('features', 'enable_payroll_module', 'Payroll Module', 'true', 'boolean', False),
            ('features', 'enable_inventory_module', 'Inventory Module', 'true', 'boolean', False),
            ('features', 'enable_banking_module', 'Banking Module', 'true', 'boolean', False),
            ('features', 'enable_taxation_module', 'Taxation Module', 'true', 'boolean', False),
            ('features', 'enable_compliance_module', 'Compliance Module', 'true', 'boolean', False),
            ('features', 'enable_multi_currency', 'Multi-Currency Support', 'true', 'boolean', False),

            # SMTP
            ('smtp', 'smtp_host', 'SMTP Host', 'smtp.sendgrid.net', 'string', False),
            ('smtp', 'smtp_port', 'SMTP Port', '587', 'integer', False),
            ('smtp', 'smtp_from_email', 'From Email', 'noreply@serenia.app', 'email', False),

            # Security
            ('security', 'max_login_attempts', 'Max Login Attempts', '5', 'integer', False),
            ('security', 'session_timeout_minutes', 'Session Timeout (minutes)', '480', 'integer', False),
            ('security', 'password_min_length', 'Minimum Password Length', '8', 'integer', False),
            ('security', 'enforce_2fa', 'Enforce Two-Factor Auth', 'false', 'boolean', False),
        ]

        created = 0
        for category, key, label, value, value_type, is_public in defaults:
            _, was_created = SystemSetting.objects.get_or_create(
                key=key,
                defaults={
                    'category': category, 'label': label, 'value': value,
                    'value_type': value_type, 'is_public': is_public,
                    'default_value': value,
                },
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ System settings ready ({created} created, {len(defaults) - created} existing)'))

    def create_default_theme(self):
        from apps.developer_mode.models import Theme

        if Theme.objects.filter(is_active=True).exists():
            self.stdout.write('  Active theme already exists — skipping.')
            return

        Theme.objects.create(name='Serenia Default', is_active=True, mode='light')
        self.stdout.write(self.style.SUCCESS('  ✓ Created default theme'))
