"""Tests for django_unmanaged_tables management command."""

from io import StringIO
from unittest.mock import Mock

import pytest
from django.apps import AppConfig
from django.core.management import call_command
from django.db.backends.base.base import BaseDatabaseWrapper
from pytest_mock import MockerFixture

from django_unmanaged_assistant.management.commands.create_unmanaged_tables import (
    Command,
    create_schema_if_not_exists,
    parse_table_name,
)
from tests.test_app.models import (
    MixedManagedModel,
    MixedUnmanagedModel,
    MixedUnmanagedModelDottedTable,
    MixedUnmanagedModelDottedTableNC,
    MixedUnmanagedModelNC,
    MixedUnmanagedModelWithFk,
    MixedUnmanagedModelWithFkNC,
    MixedUnmanagedSchemaModel,
    MixedUnmanagedSchemaModelNC,
)


@pytest.fixture
def unmanaged_models() -> list[type]:
    """
    Fixture providing all unmanaged test models.

    Returns:
        List[type]: List of unmanaged model classes.
    """
    return [
        MixedUnmanagedModel,
        MixedUnmanagedModelNC,
        MixedUnmanagedModelWithFk,
        MixedUnmanagedModelWithFkNC,
        MixedUnmanagedModelDottedTable,
        MixedUnmanagedModelDottedTableNC,
        MixedUnmanagedSchemaModel,
        MixedUnmanagedSchemaModelNC,
    ]


class TestModelProcessing:
    """Tests for processing different types of models."""

    def test_managed_models_ignored(
        self, connection: BaseDatabaseWrapper, mocker: MockerFixture
    ) -> None:
        """
        Test that managed models are ignored.

        Args:
            connection: Database connection fixture.
            mocker: Pytest mocker fixture.
        """
        command = Command()
        mock_app_config = Mock(spec=AppConfig)
        mock_app_config.get_models.return_value = [MixedManagedModel]

        command.collect_unmanaged_models(mock_app_config)
        assert len(command.models_to_process) == 0

    def test_unmanaged_models_collected(
        self,
        connection: BaseDatabaseWrapper,
        unmanaged_models: list[type],
        mocker: MockerFixture,
    ) -> None:
        """
        Test that unmanaged models are collected.

        Args:
            connection: Database connection fixture.
            unmanaged_models: List of unmanaged model classes.
            mocker: Pytest mocker fixture.
        """
        command = Command()
        mock_app_config = Mock(spec=AppConfig)
        mock_app_config.get_models.return_value = unmanaged_models

        command.collect_unmanaged_models(mock_app_config)
        assert len(command.models_to_process) == len(unmanaged_models)


class TestTableCreation:
    """Tests for table creation with different model configurations."""

    @pytest.mark.parametrize(
        "model,expected_schema,expected_table",
        [
            (MixedUnmanagedModel, "public", "mixed_unmanaged_model"),
            (
                MixedUnmanagedModelDottedTable,
                "mixed_unmanaged_model",
                "dotted_table",
            ),
            (MixedUnmanagedSchemaModel, "ALT_SCHEMA", "unmanaged_model"),
        ],
    )
    def test_table_name_parsing(
        self,
        connection: BaseDatabaseWrapper,
        model: type,
        expected_schema: str,
        expected_table: str,
    ) -> None:
        """
        Test parsing of different table name formats.

        Args:
            connection: Database connection fixture.
            model: Model class to test.
            expected_schema: Expected schema name.
            expected_table: Expected table name.
        """
        schema, table = parse_table_name(connection, model._meta.db_table)
        assert schema == expected_schema
        assert table == expected_table


class TestFieldProcessing:
    """Tests for processing different field configurations."""

    @pytest.mark.parametrize(
        "model,field_name,expected_column",
        [
            (MixedUnmanagedModel, "address", "addy"),
            (MixedUnmanagedModelNC, "address", "address"),
            (
                MixedUnmanagedModelWithFk,
                "related_model",
                "mixed_unmanaged_model_ID",
            ),
        ],
    )
    def test_column_name_resolution(
        self,
        connection: BaseDatabaseWrapper,
        model: type,
        field_name: str,
        expected_column: str,
    ) -> None:
        """
        Test resolution of column names for different field configurations.

        Args:
            connection: Database connection fixture.
            model: Model class to test.
            field_name: Name of the field to test.
            expected_column: Expected column name.
        """
        field = model._meta.get_field(field_name)
        column_name = field.db_column or field.name
        assert column_name == expected_column


class TestForeignKeyHandling:
    """Tests for handling foreign key relationships."""

    def test_foreign_key_creation(
        self, connection: BaseDatabaseWrapper, mocker: MockerFixture
    ) -> None:
        """
        Test creation of foreign key constraints.

        Args:
            connection: Database connection fixture.
            mocker: Pytest mocker fixture.
        """
        command = Command()
        schema_editor_mock = mocker.patch.object(connection, "schema_editor")

        # Test with FK model
        command.create_table_for_model(
            connection, schema_editor_mock(), MixedUnmanagedModelWithFk
        )

        # Verify FK constraint creation was attempted
        schema_editor_calls = schema_editor_mock().mock_calls
        assert any("foreign_key" in str(call) for call in schema_editor_calls)


class TestSchemaHandling:
    """Tests for handling different schema configurations."""

    @pytest.mark.parametrize(
        "model,schema",
        [
            (MixedUnmanagedSchemaModel, "ALT_SCHEMA"),
            (MixedUnmanagedModelDottedTable, "mixed_unmanaged_model"),
        ],
    )
    def test_schema_creation(
        self,
        connection: BaseDatabaseWrapper,
        mocker: MockerFixture,
        model: type,
        schema: str,
    ) -> None:
        """
        Test creation of schemas for different model configurations.

        Args:
            connection: Database connection fixture.
            mocker: Pytest mocker fixture.
            model: Model class to test.
            schema: Expected schema name.
        """
        mock_cursor = mocker.patch.object(connection, "cursor")
        schema, _ = parse_table_name(connection, model._meta.db_table)
        create_schema_if_not_exists(connection, schema)

        # Verify schema creation was attempted
        create_schema_calls = mock_cursor.return_value.__enter__.return_value.execute.call_args_list
        assert any(schema in str(call) for call in create_schema_calls)


class TestIntegration:
    """Integration tests for the management command."""

    def test_full_command_execution(
        self,
        connection: BaseDatabaseWrapper,
        unmanaged_models: list[type],
        mocker: MockerFixture,
        stdout: StringIO,
        stderr: StringIO,
    ) -> None:
        """
        Test full execution of management command with all model types.

        Args:
            connection: Database connection fixture.
            unmanaged_models: List of unmanaged model classes.
            mocker: Pytest mocker fixture.
            stdout: StringIO fixture for stdout.
            stderr: StringIO fixture for stderr.
        """
        mock_app_config = Mock(spec=AppConfig)
        mock_app_config.get_models.return_value = unmanaged_models
        mocker.patch(
            "django.apps.apps.get_app_configs", return_value=[mock_app_config]
        )

        call_command(
            "create_unmanaged_tables",
            stdout=stdout,
            stderr=stderr,
            detailed=True,
        )

        output = stdout.getvalue()
        # Verify all unmanaged models were processed
        for model in unmanaged_models:
            assert model._meta.db_table in output
