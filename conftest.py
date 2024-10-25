import pytest
from django.apps import AppConfig


class BareConfig(AppConfig):
    """Bare AppConfig class for testing."""

    name = "apps.bare_config_app"


@pytest.fixture
def empty_databases() -> list:
    """Return an empty databases dictionary."""
    return [{}, {"default": {}}]


@pytest.fixture
def app_config() -> AppConfig:
    """Return a bare AppConfig instance."""
    bare_config = BareConfig()
    return bare_config
