"""Test settings for django_unmanaged_tables."""

SECRET_KEY = "test-key"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "tests.test_app",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

USE_TZ = False
EXCLUDE_UNMANAGED_PATH = "site-packages"
ADDITIONAL_UNMANAGED_TABLE_APPS: list[str] = []
APP_TO_DATABASE_MAPPING: dict[str, str] = {}
