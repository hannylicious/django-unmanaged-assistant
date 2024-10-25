"""Mixed managed/unmanaged models (with .using()) for multi-db project."""

from django.db import models
from mixed_alt_db import managers

"""
This module contains mixed models for the multi-db project.

Classes:
    MixedManagedModel: Managed model.
    MixedManagedModelWithId: Managed model with an explicit ID.
    MixedManagedModelWithFk: Managed model with a FK.
    MixedUnmanagedModelNC: Unmanaged model with no db_column
    MixedUnmanagedModelWithFkNC: Unmanaged model with no db_column and a FK
    MixedUnmanagedModelDottedTableNC: Unmanaged model with no db_column and 
        a dotted table name.
    MixedUnmanagedSchemaModelNC: Unmanaged model with no db_column and custom
        schema.
    MixedUnmanagedModel: Unmanaged model with db_column.
    MixedUnmanagedModelWithFk: Unmanaged model with a FK.
    MixedUnmanagedModelDottedTable: Unmanaged model with a dotted table name. 
    MixedUnmanagedSchemaModel: Unmanaged model with a custom schema.
"""


class BaseMixedAltDbModel(models.Model):
    """Base model for others in this app to use custom manager."""

    objects = managers.MixedAltDbModelManager()

    class Meta:
        """Base model for mixed_alt_db to use specific db."""

        abstract = True


class MixedManagedModel(BaseMixedAltDbModel):
    """Mixed managed model."""

    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    realistic = models.BooleanField(default=True)

    class Meta:
        """Mixed managed model meta."""

        managed = True

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class MixedManagedModelWithId(BaseMixedAltDbModel):
    """Mixed managed model with explicit id field."""

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    realistic = models.BooleanField(default=True)

    class Meta:
        """Mixed managed model with id meta."""

        managed = True

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class MixedManagedModelWithFk(BaseMixedAltDbModel):
    """Mixed managed model with fk."""

    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    related_managed_model = models.ForeignKey(
        MixedManagedModel, on_delete=models.PROTECT
    )

    class Meta:
        """Mixed managed model with fk meta."""

        managed = True

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class MixedUnmanagedModelNC(BaseMixedAltDbModel):
    """Mixed unmanaged model without db_column."""

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    realistic = models.BooleanField(default=True)

    class Meta:
        """Mixed Unmanaged model without db_column meta."""

        managed = False
        db_table = "mixed_unmanaged_model_nc"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class MixedUnmanagedModelWithFkNC(BaseMixedAltDbModel):
    """Mixed unmanaged model with FK without db_column."""

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    realistic = models.BooleanField(default=True)
    related_model = models.ForeignKey(
        MixedUnmanagedModelNC, on_delete=models.PROTECT
    )

    class Meta:
        """Mixed Unmanaged model with FK without db_column meta."""

        managed = False
        db_table = "mixed_unmanaged_model_fk_nc"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class MixedUnmanagedModelDottedTableNC(BaseMixedAltDbModel):
    """Mixed unmanaged model with a dotted db table without db_column."""

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    realistic = models.BooleanField(default=True)

    class Meta:
        """Mixed unmanaged model with a dotted db table without db_column."""

        managed = False
        db_table = "mixed_unmanaged_model.dotted_table_nc"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class MixedUnmanagedSchemaModelNC(BaseMixedAltDbModel):
    """Mixed unmanaged model with a specific schema and no db_column."""

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    realistic = models.BooleanField(default=True)

    class Meta:
        """Unmanaged model with a specific schema and no db_column meta."""

        managed = False
        db_table = "[ALT_SCHEMA].[unmanaged_model_nc]"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class MixedUnmanagedModel(BaseMixedAltDbModel):
    """Mixed unmanaged model with db_column."""

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


class MixedUnmanagedModelWithFk(BaseMixedAltDbModel):
    """Mixed unmanaged model with FK with db_column."""

    id = models.IntegerField(db_column="id", primary_key=True)
    name = models.CharField(db_column="name", max_length=100)
    address = models.CharField(db_column="addy", max_length=255)
    realistic = models.BooleanField(db_column="real", default=True)
    related_model = models.ForeignKey(
        MixedUnmanagedModel,
        db_column="mixed_unmanaged_model_ID",
        on_delete=models.PROTECT,
    )

    class Meta:
        """Mixed Unmanaged model with FK with db_column meta."""

        managed = False
        db_table = "mixed_unmanaged_model_fk"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class MixedUnmanagedModelDottedTable(BaseMixedAltDbModel):
    """Mixed unmanaged model with a dotted db table with db_column."""

    id = models.IntegerField(db_column="id", primary_key=True)
    name = models.CharField(db_column="name", max_length=100)
    address = models.CharField(db_column="addy", max_length=255)
    realistic = models.BooleanField(db_column="real", default=True)

    class Meta:
        """Mixed unmanaged model with a dotted db table with db_column."""

        managed = False
        db_table = "mixed_unmanaged_model.dotted_table"

    def __str__(self) -> str:
        """Return name."""
        return f"{self.name}"


class MixedUnmanagedSchemaModel(BaseMixedAltDbModel):
    """Mixed unmanaged model with a specific schema and db_column."""

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
