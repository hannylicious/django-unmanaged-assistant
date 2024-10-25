"""Manager for the multi-db venv_alt_db app."""

from django.db import models


class UnmanagedVenvModelManager(models.Manager):
    """Manager with .using() to specify database."""

    def get_queryset(self) -> models.QuerySet:
        """Return queryset using a specific db."""
        return super().get_queryset().using("alternate")
