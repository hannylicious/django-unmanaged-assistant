"""Manager for the multi-db mixed_app_alt_db app."""

from django.db import models


class MixedAltDbModelManager(models.Manager):
    """Manager with .using() to specify database."""

    def get_queryset(self) -> models.QuerySet:
        """Return queryset using a specific db."""
        return super().get_queryset().using("alternate")
