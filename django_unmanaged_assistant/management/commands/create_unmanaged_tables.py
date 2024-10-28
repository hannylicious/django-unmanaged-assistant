"""Management command to create tables for unmanaged models in the project."""

import re
from contextlib import ExitStack, contextmanager
from typing import TextIO

from django.apps import AppConfig, apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from django.db import connections, models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.models import Field, Model
from django.db.utils import ProgrammingError


def is_app_eligible(app_config: AppConfig) -> bool:
    """
    Check if the app is eligible for processing.

    Args:
        app_config (AppConfig): The Django app configuration.

    Returns:
        bool: True if the app is eligible for processing, False otherwise.
    """
    app_name = app_config.name.split(".")[-1]
    exclude_path = getattr(settings, "EXCLUDE_UNMANAGED_PATH", "site-packages")
    is_local_app = exclude_path not in app_config.path
    is_additional_app = app_name in getattr(
        settings, "ADDITIONAL_UNMANAGED_TABLE_APPS", []
    )
    return is_local_app or is_additional_app


def get_default_schema(
    connection: BaseDatabaseWrapper,
) -> str | None:
    """
    Get the default schema for the database connection.

    Args:
        connection (BaseDatabaseWrapper): The database connection.

    Returns:
        str: The default schema name.
    """
    if connection.vendor == "postgresql":
        return "public"
    elif connection.vendor == "microsoft":
        return "dbo"
    elif connection.vendor == "sqlite":
        return "main"
    else:
        return None


def create_schema_if_not_exists(
    connection: BaseDatabaseWrapper, schema: str
) -> None:
    """
    Create the schema if it doesn't exist.

    Args:
        connection (BaseDatabaseWrapper): The database connection.
        schema (str): The name of the schema to create.

    Raises:
        ValueError: If the schema name contains invalid characters.
        ProgrammingError: If there's an error executing the SQL.
    """
    # Validate the schema name
    if not re.match(r"^[A-Za-z0-9_.]+$", schema):
        raise ValueError(
            f"Invalid schema name: {schema}. Only alphanumeric characters, underscores, and periods are allowed."  # noqa: E501
        )

    with connection.cursor() as cursor:
        # TODO: Handle schema selection and creation for database backends
        if connection.vendor == "sqlite":
            # SQLite does not support schemas in the same way as other
            # databases, it would require a separate database.
            return
        if connection.vendor == "postgresql":
            from psycopg2 import sql

            cursor.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(schema)
                )
            )
        elif connection.vendor in ["microsoft", "mssql"]:
            # TODO: Verify Microsoft SQL Server schema creation
            cursor.execute(
                "SELECT 1 FROM sys.schemas WHERE name = %s", [schema]
            )
            if cursor.fetchone() is None:
                cursor.execute(f"CREATE SCHEMA [{schema}]")
        else:
            raise NotImplementedError(
                f"Schema creation not implemented for {connection.vendor}"
            )


def table_exists(
    connection: BaseDatabaseWrapper,
    schema: str,
    table: str,
) -> bool:
    """
    Check if a table exists in the specified schema.

    This method queries thd db to determine if a table with the given name
    exists in the specified schema.

    Args:
        connection (BaseDatabaseWrapper): The database connection.
        schema (str): The database schema name.
        table (str): The database table name.

    Returns:
        bool: True if the table exists, False otherwise.
    """
    with connection.cursor() as cursor:
        if connection.vendor == "sqlite":
            cursor.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table' AND name = %s
            """,
                [table],
            )
        elif connection.vendor == "postgresql":
            cursor.execute(
                """
                SELECT 1
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """,
                [schema, table],
            )
        elif connection.vendor == "microsoft":
            cursor.execute(
                """
                SELECT 1
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """,
                [schema, table],
            )
        return cursor.fetchone() is not None


def column_exists(
    connection: BaseDatabaseWrapper,
    schema: str,
    table: str,
    column_name: str,
) -> bool:
    """
    Check if a column exists in the specified table and schema.

    This method queries the INFORMATION_SCHEMA.COLUMNS view to determine
    if a column with the given name exists in the specified table and
    schema.

    Args:
        connection (BaseDatabaseWrapper): The database connection.
        schema (str): The database schema name.
        table (str): The database table name.
        column_name (str): The name of the column to check for existence.

    Returns:
        bool: True if the column exists, False otherwise.

    Raises:
        django.db.Error: If there's an error executing the SQL query.
    """
    with connection.cursor() as cursor:
        if connection.vendor == "sqlite":
            cursor.execute(
                """
                SELECT 1
                FROM pragma_table_info(%s)
                WHERE name = %s
            """,
                [table, column_name],
            )
        elif connection.vendor == "postgresql":
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = %s
                  AND column_name = %s
            """,
                [schema, table, column_name],
            )
        elif connection.vendor == "microsoft":
            cursor.execute(
                """
                SELECT 1
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
            """,
                [schema, table, column_name],
            )
        return cursor.fetchone() is not None


def get_field_db_type(connection: BaseDatabaseWrapper, field: Field) -> str:
    """
    Get the database type for a Django model field.

    Args:
        connection (BaseDatabaseWrapper): The database connection.
        field (Field): The Django model field.

    Returns:
        str: The database type for the field.
    """
    return field.db_type(connection)


def types_are_compatible(existing_type: str, expected_type: str) -> bool:
    """
    Check if two database column types are compatible.

    This method checks if the existing database column type is compatible
    with the expected type based on the model field type.

    Args:
        existing_type (str): The existing database column type.
        expected_type (str): The expected database column type.

    Returns:
        bool: True if the types are compatible, False otherwise.
    """
    existing_type = existing_type.lower() if existing_type else ""
    expected_type = expected_type.lower() if expected_type else ""

    compatible_types = {
        "int": ["int", "integer", "smallint", "bigint"],
        "varchar": ["varchar", "char", "text", "nvarchar", "nchar"],
        "float": ["float", "real", "double precision"],
        "decimal": ["decimal", "numeric"],
        "datetime": ["datetime", "timestamp", "date", "time"],
        "bool": ["bool", "boolean", "bit"],
    }

    for db_type, compatible_list in compatible_types.items():
        if (
            existing_type in compatible_list
            and expected_type in compatible_list
        ):
            return True

    return False


def parse_table_name(
    connection: BaseDatabaseWrapper, table_name: str
) -> tuple:
    """
    Parse the table name into schema and table parts.

    Returns a tuple of (schema, table).

    If the table name is not qualified with a schema, the default schema
    for the connection is used.

    Examples:
    - [schema].[table] -> (schema, table)
    - schema.table -> (schema, table)
    - table -> (default_schema, table)

    Args:
        connection (BaseDatabaseWrapper): The database connection.
        table_name (str): the table name to parse

    Returns:
        tuple: (schema, table)
    """
    if "[" in table_name and "]" in table_name:
        parts = table_name.split(".", 1)
        schema = parts[0].strip("[]")
        table = parts[1].strip("[]")
    elif "." in table_name:
        schema, table = table_name.split(".", 1)
    else:
        schema = get_default_schema(connection)
        table = table_name
    schema = schema.strip('"').strip("'")
    table = table.strip('"').strip("'")
    return schema, table


def get_column_type(
    connection: BaseDatabaseWrapper,
    schema: str,
    table: str,
    column_name: str,
) -> str | None:
    """
    Get the data type of column in the database.

    Args:
        connection (BaseDatabaseWrapper): The database connection.
        schema (str): The database schema name.
        table (str): The database table name.
        column_name (str): The name of the database column.

    Returns:
        str: The data type of the column, or None if the column does not
        exist.
    """
    with connection.cursor() as cursor:
        if connection.vendor == "sqlite":
            cursor.execute(
                """
                SELECT type
                FROM pragma_table_info(%s)
                WHERE name = %s
            """,
                [table, column_name],
            )
        elif connection.vendor == "postgresql":
            cursor.execute(
                """
                SELECT DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
            """,
                [schema, table, column_name],
            )
        elif connection.vendor == "microsoft":
            cursor.execute(
                """
                SELECT DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
            """,
                [schema, table, column_name],
            )
        result = cursor.fetchone()
        return result[0] if result else None


def get_formatted_table_name(
    connection: BaseDatabaseWrapper, schema: str, table: str
) -> str:
    """
    Format the table name correctly based on the database backend.

    Args:
        connection (BaseDatabaseWrapper): The database connection.
        schema (str): The schema name.
        table (str): The table name.

    Returns:
        str: The correctly formatted table name for the specific database.
    """
    if connection.vendor == "postgresql":
        return f'"{schema}"."{table}"'
    elif connection.vendor in ["microsoft", "mssql"]:
        return f"[{schema}].[{table}]"
    else:
        # For other databases, return the unquoted version
        return f"{schema}.{table}"


@contextmanager
def temporary_table_name(
    model: type[Model], connection: BaseDatabaseWrapper
) -> str:
    """
    Context manager to temporarily change the db_table name of a model.

    Args:
        model (type[Model]): The Django model class.
        connection (BaseDatabaseWrapper): The database connection.

    Yields:
        str: The formatted table name for the model.
    """
    original_db_table = model._meta.db_table
    if not connection.vendor == "sqlite":
        schema, table = parse_table_name(connection, original_db_table)
        formatted_table_name = get_formatted_table_name(
            connection, schema, table
        )
        model._meta.db_table = formatted_table_name
    try:
        yield
    finally:
        model._meta.db_table = original_db_table


def restore_foreign_keys(original_settings: list[tuple]) -> None:
    """
    Restore original FK settings.

    Args:
        original_settings (list[tuple]): Settings to restore
    """
    for field, db_constraint, on_delete in original_settings:
        field.db_constraint = db_constraint
        field.remote_field.on_delete = on_delete


def handle_foreign_keys(model: type[Model]) -> list[tuple]:
    """
    Temporarily disable FK constraints for unmanaged models.

    Args:
        model (type[Model]): The model to process

    Returns:
        list[tuple]: List of original FK settings to restore
    """
    if model._meta.managed:
        return []

    original_settings = []
    for field in model._meta.fields:
        if isinstance(field, models.ForeignKey):
            original_settings.append(
                (field, field.db_constraint, field.remote_field.on_delete)
            )
            field.db_constraint = False
            field.remote_field.on_delete = models.DO_NOTHING
    return original_settings


class Command(BaseCommand):
    """Command to create tables for unmanaged models in the project."""

    help = "Create tables for unmanaged models in the project"

    def __init__(
        self,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
        no_color: bool = False,
        force_color: bool = False,
    ) -> None:
        """
        Initialize the command.

        Args:
            stdout (Optional[TextIO]): Stream to use as stdout. Defaults: None.
            stderr (Optional[TextIO]): Stream to use as stderr. Defaults: None.
            no_color (bool): If True, disable colored output. Defaults: False.
            force_color (bool): If True, force colored output. Defaults: False.

        Returns:
            None
        """
        super().__init__(stdout, stderr, no_color, force_color)
        self.verbose: bool | None = None
        self.connection = None
        self.models_to_process = []

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add arguments to the command.

        Args:
            parser (CommandParser): The command parser

        Returns:
            None
        """
        parser.add_argument(
            "-d",
            "--detailed",
            action="store_true",
            help="Increase output verbosity",
        )

    def handle(self, *args: str, **options: dict[str, str]) -> None:
        """
        Handle the management command.

        Iterate over all Django app configurations and processes those that
        do not start with the path of the 'django_unmanaged_assistant' app.

        Args:
            *args: Variable length argument list.
            **options: Arbitrary keyword arguments.

        Returns:
            None
        """
        self.verbose = options["detailed"]
        for app_config in apps.get_app_configs():
            if is_app_eligible(app_config):
                self.collect_unmanaged_models(app_config)

        self.process_models()

    def collect_unmanaged_models(self, app_config: AppConfig) -> None:
        """
        Collect unmanaged models from the given app configuration.

        Args:
            app_config (AppConfig): The Django app configuration.

        Returns:
            None
        """
        for model in app_config.get_models():
            if not model._meta.managed:
                self.models_to_process.append(model)

    def process_models(self) -> None:
        """
        Process the unmanaged models.

        This method groups the models by database connection and processes
        each model for each connection.

        Returns:
            None
        """
        models_by_connection = {}
        for model in self.models_to_process:
            # Get the default database
            db_alias = "default"
            # TODO: Add support for dbrouters if they exist?
            if settings.APP_TO_DATABASE_MAPPING:
                db_name = settings.APP_TO_DATABASE_MAPPING.get(
                    model._meta.app_label
                )
                if db_name:
                    db_alias = db_name
            connection = connections[db_alias]
            if connection not in models_by_connection:
                models_by_connection[connection] = []
            models_by_connection[connection].append(model)

        # Process models for each connection
        for connection, models in models_by_connection.items():
            self.connection = connection
            with connection.schema_editor() as schema_editor:
                with ExitStack() as stack:
                    # Apply temporary table names to all models
                    for model in models:
                        stack.enter_context(
                            temporary_table_name(model, connection)
                        )

                    # Now process each model
                    for model in models:
                        self.create_table_for_model(
                            connection, schema_editor, model
                        )

    def create_model_table(
        self,
        schema_editor: BaseDatabaseSchemaEditor,
        model: type[Model],
        schema: str,
        table: str,
    ) -> bool:
        """
        Create the table for the model if it doesn't exist.

        Args:
            schema_editor: The schema editor
            model: The model to create a table for
            schema: Database schema name
            table: Table name

        Returns:
            bool: True if table created or exists, False if error
        """
        if not table_exists(self.connection, schema, table):
            if self.verbose:
                self.stdout.write(
                    self.style.SUCCESS(f"Creating table for {model.__name__}")
                )
            try:
                schema_editor.create_model(model)
                return True
            except ProgrammingError as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Error creating table for {model.__name__}: {str(e)}"
                    )
                )
                return False
        else:
            if self.verbose:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Table for {model.__name__} already exists"
                    )
                )
            return True

    def create_table_for_model(
        self,
        connection: BaseDatabaseWrapper,
        schema_editor: BaseDatabaseSchemaEditor,
        model: type[Model],
    ) -> None:
        """
        Create a table for the given model if it does not exist.

        For unmanaged models, creates FKs without database constraints.
        """
        # Handle FK constraints for unmanaged models
        original_fk_settings = handle_foreign_keys(model)

        try:
            # Get table info
            table_name = model._meta.db_table
            schema, table = parse_table_name(self.connection, table_name)

            if self.verbose:
                self.stdout.write(
                    f"Processing table '{table}' in schema '{schema}'"
                )

            # Ensure schema exists
            if schema:
                create_schema_if_not_exists(self.connection, schema)

            # Create table if needed
            if not self.create_model_table(
                schema_editor, model, schema, table
            ):
                return

            # Process fields
            for field in model._meta.fields:
                self.process_field(
                    connection, schema_editor, model, schema, table, field
                )

        finally:
            # Restore original FK settings
            restore_foreign_keys(original_fk_settings)

    def process_field(
        self,
        connection: BaseDatabaseWrapper,
        schema_editor: BaseDatabaseSchemaEditor,
        model: type[Model],
        schema: str,
        table: str,
        field: Field,
    ) -> None:
        """Process a field for the given model and table."""
        # Get the base column name from the field
        column_name = field.db_column or field.name

        # For foreign key fields, be smarter about the column name
        if isinstance(field, models.ForeignKey):
            # If db_column is set, use it exactly as specified
            if field.db_column:
                column_name = field.db_column
            # If no db_column is set, append '_id' only if it's not already there
            elif not column_name.endswith("_id"):
                column_name += "_id"

        if self.verbose:
            self.stdout.write(
                f"Checking column '{column_name}' in schema '{schema}', table '{table}'"
            )

        if not column_exists(connection, schema, table, column_name):
            if self.verbose:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Adding column {column_name} to {model.__name__}"
                    )
                )
            try:
                # Store original db_column
                original_db_column = field.db_column
                # Temporarily set db_column to match what we want
                field.db_column = column_name

                schema_editor.add_field(model, field)

                # Restore original db_column
                field.db_column = original_db_column

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Error adding column {column_name}: {str(e)}"
                    )
                )
        else:
            if self.verbose:
                self.check_column_compatibility(
                    connection, model, schema, table, field, column_name
                )

    def check_column_compatibility(
        self,
        connection: BaseDatabaseWrapper,
        model: type[Model],
        schema: str,
        table: str,
        field: Field,
        column_name: str,
    ) -> None:
        """
        Check if existing database column type is compatible with the field.

        This method compares the existing database column type with the
        expected type based on the model field. It outputs a warning if the
        types are incompatible, and a success message if they are compatible.

        Args:
            connection (BaseDatabaseWrapper): The database
            connection.
            model (type[Model]): The Django model class containing the field.
            schema (str): The database schema name.
            table (str): The database table name.
            field (Field): The Django model field to check.
            column_name (str): The name of the database column.

        Returns:
            None

        Side effects:
            Writes output to self.stdout using self.style for formatting.
        """
        existing_type = get_column_type(connection, schema, table, column_name)
        expected_type = get_field_db_type(connection, field)
        if not types_are_compatible(existing_type, expected_type):
            self.stdout.write(
                self.style.WARNING(
                    f"Column {column_name} in {model.__name__} has type {existing_type}, "  # noqa: E501
                    f"but the model field type is {expected_type}. Consider manual migration."  # noqa: E501
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Column {column_name} exists in {model.__name__} with compatible type {existing_type}"  # noqa: E501
                )
            )
