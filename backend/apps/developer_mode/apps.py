from django.apps import AppConfig


class DeveloperModeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.developer_mode'
    verbose_name = 'Developer Mode (Super Admin)'
