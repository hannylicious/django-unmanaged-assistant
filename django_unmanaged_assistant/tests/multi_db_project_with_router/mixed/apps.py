from django.apps import AppConfig


class MixedConfig(AppConfig):
    """App config for mixed app alt db."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "mixed"
