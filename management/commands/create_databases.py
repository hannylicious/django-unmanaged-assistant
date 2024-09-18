"""Command to create databases from settings if they do not exist."""

from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django management command to create databases specified in settings."""

    help = "Create databases specified in Django settings if they do not exist"

    def handle(self, *args: str, **options: dict[str, str]) -> None:
        """
        Execute the command to create databases.

        Args:
            *args: Variable length argument list.
            **options: Arbitrary keyword arguments.

        Returns:
            None
        """
        for db_name, db_settings in settings.DATABASES.items():
            self.stdout.write(f"Checking database '{db_name}'...")

            try:
                self.create_database_if_not_exists(db_name, db_settings)
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Error creating database '{db_name}': {str(e)}"
                    )
                )

    def create_database_if_not_exists(
        self, db_name: str, db_settings: dict[str, Any]
    ) -> None:
        """
        Create a database if it doesn't exist based on the database engine.

        Args:
            db_name (str): The name of the database.
            db_settings (Dict[str, Any]): The database settings dictionary.

        Raises:
            ValueError: If the database engine is not supported or if the
            database name is not specified.

        Returns:
            None
        """
        engine = db_settings.get("ENGINE", "")

        if "sqlite3" in engine:
            self.stdout.write(
                self.style.SUCCESS(
                    f"SQLite database '{db_name}' will be created automatically when needed."  # noqa: E501
                )
            )
            return

        db_name = db_settings.get("NAME")
        if not db_name:
            raise ValueError(
                f"Database name for '{db_name}' is not specified in settings."
            )

        if "postgresql" in engine:
            self.create_postgresql_db(db_settings)
        elif "mysql" in engine:
            self.create_mysql_db(db_settings)
        elif "microsoft" in engine or "mssql" in engine:
            self.create_mssql_db(db_settings)
        else:
            raise ValueError(f"Unsupported database engine: {engine}")

    def create_postgresql_db(self, db_settings: dict[str, Any]) -> None:
        """
        Create a PostgreSQL database if it doesn't exist.

        Args:
            db_settings (Dict[str, Any]): The database settings dictionary.

        Returns:
            None
        """
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        db_name = db_settings["NAME"]
        user = db_settings.get("USER", "")
        password = db_settings.get("PASSWORD", "")
        host = db_settings.get("HOST", "")
        port = db_settings.get("PORT", "")

        conn = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (db_name,),
        )
        exists = cur.fetchone()
        if not exists:
            cur.execute(f"CREATE DATABASE {db_name}")
            self.stdout.write(
                self.style.SUCCESS(f"Created PostgreSQL database '{db_name}'")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"PostgreSQL database '{db_name}' already exists"
                )
            )
        cur.close()
        conn.close()

    def create_mysql_db(self, db_settings: dict[str, Any]) -> None:
        """
        Create a MySQL database if it doesn't exist.

        Args:
            db_settings (Dict[str, Any]): The database settings dictionary.

        Returns:
            None
        """
        import MySQLdb

        db_name = db_settings["NAME"]
        user = db_settings.get("USER", "")
        password = db_settings.get("PASSWORD", "")
        host = db_settings.get("HOST", "")
        port = int(db_settings.get("PORT", 3306))

        conn = MySQLdb.connect(
            user=user, passwd=password, host=host, port=port
        )
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        self.stdout.write(
            self.style.SUCCESS(
                f"Created (if not exists) MySQL database '{db_name}'"
            )
        )
        cur.close()
        conn.close()

    def create_mssql_db(self, db_settings: dict[str, Any]) -> None:
        """
        Create a Microsoft SQL Server database if it doesn't exist.

        Args:
            db_settings (Dict[str, Any]): The database settings dictionary.

        Returns:
            None
        """
        import pyodbc

        db_name = db_settings["NAME"]
        user = db_settings.get("USER", "")
        password = db_settings.get("PASSWORD", "")
        host = db_settings.get("HOST", "")
        driver = db_settings.get("OPTIONS", {}).get(
            "driver", "ODBC Driver 18 for SQL Server"
        )
        extra_params = db_settings.get("OPTIONS", {}).get("extra_params", "")
        if extra_params:
            conn_str = f"DRIVER={{{driver}}};SERVER={host};DATABASE=master;UID={user};PWD={password};{extra_params}"  # noqa: E501
        else:
            conn_str = f"DRIVER={{{driver}}};SERVER={host};DATABASE=master;UID={user};PWD={password}"  # noqa: E501

        conn = pyodbc.connect(conn_str, autocommit=True)
        cur = conn.cursor()

        cur.execute(
            f"SELECT name FROM sys.databases WHERE name = N'{db_name}'"
        )
        exists = cur.fetchone()

        if not exists:
            cur.execute(f"CREATE DATABASE [{db_name}]")
            self.stdout.write(
                self.style.SUCCESS(f"Created SQL Server database '{db_name}'")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"SQL Server database '{db_name}' already exists"
                )
            )

        cur.close()
        conn.close()
