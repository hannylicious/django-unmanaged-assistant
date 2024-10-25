from django.apps import AppConfig


class ManagedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "managed"
