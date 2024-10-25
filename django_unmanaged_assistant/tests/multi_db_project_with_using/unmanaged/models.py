"""Unmanaged models in alternate DB for multi-db project."""

from django.db import models
from unmanaged import managers

"""
This module contains mixed models for the multi-db project.

Django does not support cross-db queries so we cannot have FK's in these
models!

Classes:
    UnmanagedModelNC: Unmanaged model with no db_column
    UnmanagedModelDottedTableNC: Unmanaged model with no db_column and 
        a dotted table name.
    UnmanagedSchemaModelNC: Unmanaged model with no db_column and custom
        schema.
    UnmanagedModel: Unmanaged model with db_column.
    UnmanagedModelDottedTable: Unmanaged model with a dotted table name. 
    UnmanagedSchemaModel: Unmanaged model with a custom schema.
"""


class BaseUnmanagedModel(models.Model):
    """Base model for others in this app to use custom manager."""

    objects = managers.UnmanagedModelManager()

    class Meta:
        """Base model for unmanaged_alt_db to use specific db."""

        abstract = True


class UnmanagedModelNC(BaseUnmanagedModel):
    """Unmanaged model without db_column."""

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    realistic = models.BooleanField(default=True)

    class Meta:
        """Mixed Unmanaged model meta."""

        managed = False
        db_table = "mixed_unmanaged_model_nc"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class UnmanagedModelDottedTableNC(BaseUnmanagedModel):
    """Unmanaged model with a dotted db table without db_column."""

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    realistic = models.BooleanField(default=True)

    class Meta:
        """Unmanaged model with a dotted db table."""

        managed = False
        db_table = "mixed_unmanaged_model.dotted_table_nc"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class UnmanagedSchemaModel(BaseUnmanagedModel):
    """Unmanaged model with a specific schema and no db_column."""

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    realistic = models.BooleanField(default=True)

    class Meta:
        """Unmanaged model three meta."""

        managed = False
        db_table = "[ALT_SCHEMA].[unmanaged_model_nc]"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class UnmanagedModel(BaseUnmanagedModel):
    """Unmanaged model with db_column."""

    id = models.IntegerField(db_column="id", primary_key=True)
    name = models.CharField(db_column="name", max_length=100)
    address = models.CharField(db_column="addy", max_length=255)
    realistic = models.BooleanField(db_column="real", default=True)

    class Meta:
        """Mixed Unmanaged model with db_column meta."""

        managed = False
        db_table = "mixed_unmanaged_model"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class UnmanagedModelDottedTable(BaseUnmanagedModel):
    """Unmanaged model with a dotted db table with db_column."""

    id = models.IntegerField(db_column="id", primary_key=True)
    name = models.CharField(db_column="name", max_length=100)
    address = models.CharField(db_column="addy", max_length=255)
    realistic = models.BooleanField(db_column="real", default=True)

    class Meta:
        """Unmanaged model with a dotted db table with db_column."""

        managed = False
        db_table = "mixed_unmanaged_model.dotted_table"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class UnmanagedSchemaModel(BaseUnmanagedModel):
    "Unmanaged model with a specific schema and db_column." ""

    id = models.IntegerField(db_column="id", primary_key=True)
    name = models.CharField(db_column="name", max_length=100)
    address = models.CharField(db_column="addy", max_length=255)
    realistic = models.BooleanField(db_column="real", default=True)

    class Meta:
        """Unmanaged model with a specific schema and db_column meta."""

        managed = False
        db_table = "[ALT_SCHEMA].[unmanaged_model]"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"
