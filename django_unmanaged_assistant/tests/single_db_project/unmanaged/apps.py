from django.apps import AppConfig


class UnmanagedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "unmanaged"
