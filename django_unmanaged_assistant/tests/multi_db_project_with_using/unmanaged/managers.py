"""Managers for the multi-db unmanaged_app app."""

from django.db import models


class UnmanagedModelManager(models.Manager):
    """Manager for unmanaged models on alt db with .using()."""

    def get_queryset(self) -> models.QuerySet:
        """Return queryset using a specific db."""
        return super().get_queryset().using("alternate")
