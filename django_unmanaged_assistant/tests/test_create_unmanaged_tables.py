import pytest
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import DEFAULT_DB_ALIAS, ConnectionHandler


def test_connection_handler_no_databases(empty_databases: list) -> None:
    """
    Test db connection handler with no databases.

    Empty DATABASES and empty 'default' settings default to the dummy
    backend.
    """
    for databases in empty_databases:
        conns = ConnectionHandler(databases)
        assert (
            conns[DEFAULT_DB_ALIAS].settings_dict["ENGINE"]
            == "django.db.backends.dummy"
        )
        with pytest.raises(ImproperlyConfigured):
            conns[DEFAULT_DB_ALIAS].ensure_connection()


def test_is_app_eligible_default_app_config() -> None:
    """Test if app is eligible for unmanaged tables creation."""

    class MyAdmin(AppConfig):
        name = "Test"
        verbose_name = "Admin sweet admin."
        path = "/test"

    ac = MyAdmin("Test", "test")
    assert ac.name == "Test"
    assert ac.path == "/test"
    breakpoint()
