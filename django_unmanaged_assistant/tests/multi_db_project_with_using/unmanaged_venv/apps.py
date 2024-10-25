from django.apps import AppConfig


class UnmanagedVenvConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "unmanaged_venv"
    path = "site-packages/unmanaged_venv"
