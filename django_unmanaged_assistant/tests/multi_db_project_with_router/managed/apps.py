from django.apps import AppConfig


class ManagedConfig(AppConfig):
    """App config for managed app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "managed"
