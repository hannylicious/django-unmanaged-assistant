"""Test configuration for django_unmanaged_assistant."""

import os
from collections.abc import Generator
from io import StringIO
from typing import Any

import django
import pytest
from django.conf import settings
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper

# Configure Django settings before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
django.setup()

# Now we can import models
from tests.test_app.models import (
    MixedUnmanagedModel,
    MixedUnmanagedModelDottedTable,
    MixedUnmanagedModelDottedTableNC,
    MixedUnmanagedModelNC,
    MixedUnmanagedModelWithFk,
    MixedUnmanagedModelWithFkNC,
    MixedUnmanagedSchemaModel,
    MixedUnmanagedSchemaModelNC,
)


def pytest_configure() -> None:
    """Configure Django settings for tests."""
    # Settings are already configured above, so this is just a hook for pytest
    pass


@pytest.fixture(scope="session")
def django_db_setup() -> None:
    """Configure database for tests."""
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }


@pytest.fixture
def connection() -> BaseDatabaseWrapper:
    """
    Fixture providing database connection.

    Returns:
        BaseDatabaseWrapper: Django database connection object.
    """
    return connections["default"]


@pytest.fixture
def stdout() -> Generator[StringIO, None, None]:
    """
    Provide StringIO object for capturing stdout.

    Yields:
        StringIO: String buffer for stdout capture.
    """
    output = StringIO()
    yield output
    output.close()


@pytest.fixture
def stderr() -> Generator[StringIO, None, None]:
    """
    Provide StringIO object for capturing stderr.

    Yields:
        StringIO: String buffer for stderr capture.
    """
    output = StringIO()
    yield output
    output.close()


@pytest.fixture
def unmanaged_models() -> list[Any]:
    """
    Fixture providing all unmanaged test models.

    Returns:
        List[Any]: List of unmanaged model classes.
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
