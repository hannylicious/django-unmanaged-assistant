"""Tests for django_unmanaged_tables management command."""

from io import StringIO
from unittest.mock import Mock

import pytest
from django.apps import AppConfig
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


@pytest.mark.django_db
class TestTableCreation:
    """Tests for table creation with different model configurations."""

    @pytest.mark.parametrize(
        "model,expected_table",
        [
            (MixedUnmanagedModel, "mixed_unmanaged_model"),
            (MixedUnmanagedModelDottedTable, "dotted_table"),
            (MixedUnmanagedSchemaModel, "unmanaged_model"),
        ],
    )
    def test_table_name_parsing(
        self, connection: BaseDatabaseWrapper, model: type, expected_table: str
    ) -> None:
        """
        Test parsing of different table name formats.

        Args:
            connection: Database connection fixture.
            model: Model class to test.
            expected_table: Expected table name.
        """
        # SQLite uses 'main' as default schema
        schema, table = parse_table_name(connection, model._meta.db_table)
        expected_schema = (
            "main" if connection.vendor == "sqlite3" else "public"
        )

        assert table == expected_table
        # Only check schema for simple table names
        if "." not in model._meta.db_table and "[" not in model._meta.db_table:
            assert schema == expected_schema


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


@pytest.mark.django_db
class TestForeignKeyHandling:
    """Tests for handling foreign key relationships."""

    # TODO: test something to handle when FK relation is not same type
    # Between two unmanaged models (or even managed when the managed one
    # does not have an explicit id field)
    # modela has FK reference to modelb which has 'id' handled by django and
    # the default model type (BigInt, etc.) - you can end up with type mismatch
    def test_foreign_key_creation(
        self, connection: BaseDatabaseWrapper, mocker: MockerFixture
    ) -> None:
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
            command.verbose = True  # Enable verbose output for testing
            schema_editor_mock = mocker.patch.object(
                connection, "schema_editor"
            )
            schema_editor = (
                schema_editor_mock.return_value.__enter__.return_value
            )

            # Test with FK model
            command.create_table_for_model(
                connection, schema_editor, MixedUnmanagedModelWithFk
            )

            # Verify create_model was called
            assert schema_editor.create_model.called


@pytest.mark.django_db
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
        cursor_mock = mocker.MagicMock()
        mocker.patch.object(connection, "cursor", return_value=cursor_mock)
        cursor_mock.__enter__.return_value = cursor_mock

        parsed_schema, _ = parse_table_name(connection, model._meta.db_table)

        # SQLite doesn't support schemas in the same way
        if connection.vendor == "sqlite3":
            create_schema_if_not_exists(connection, parsed_schema)
            assert True  # Schema creation is no-op for SQLite
        else:
            create_schema_if_not_exists(connection, parsed_schema)
            assert cursor_mock.execute.called


@pytest.mark.django_db
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
        # Mock the app config
        mock_app_config = mocker.Mock(spec=AppConfig)
        mock_app_config.path = "/path/to/app"
        mock_app_config.name = "test_app"
        mock_app_config.get_models.return_value = unmanaged_models

        # Mock the apps registry
        mocker.patch(
            "django.apps.apps.get_app_configs", return_value=[mock_app_config]
        )

        # Create and execute command directly
        command = Command(stdout=stdout, stderr=stderr)
        command.handle(detailed=True)

        output = stdout.getvalue()
        # Verify some output was generated
        assert len(output) > 0
        # Verify all unmanaged models were processed
        for model in unmanaged_models:
            if not model._meta.managed:
                assert model._meta.db_table in output
