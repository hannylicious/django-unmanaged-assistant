"""Managed models for multi-db project."""

from django.db import models

"""
This module contains managed models for the multi-db project.

Classes:
    ManagedModel: A standard managed model.
    ManagedModelWithId: A managed model with an explicit ID.
    ManagedModelWithFk: A managed model with a FK.
"""


class ManagedModel(models.Model):
    """Managed model (default)."""

    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    realistic = models.BooleanField(default=True)

    class Meta:
        """Managed model meta."""

        managed = True

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class ManagedModelWithId(models.Model):
    """Managed model with explicit ID."""

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    realistic = models.BooleanField(default=True)

    class Meta:
        """Managed model with id meta."""

        managed = True

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class ManagedModelWithFk(models.Model):
    """Managed model with fk."""

    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    related_managed_model = models.ForeignKey(
        ManagedModel, on_delete=models.PROTECT
    )

    class Meta:
        """Managed model with fk meta."""

        managed = True

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"
