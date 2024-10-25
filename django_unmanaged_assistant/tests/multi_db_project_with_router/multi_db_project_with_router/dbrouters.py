"""Manage routing for the multi_db_project_with_router project."""


class ApplicationRouter:
    """
    A router to control all database operations.

    Works with models in the multi_db_project_with_router application.
    """

    # Define app labels
    alternate_db_apps = {"mixed", "unmanaged", "unmanaged_venv"}

    def db_for_read(self, model, **hints):
        """Return the alternate db for read operations."""
        if model._meta.app_label in self.alternate_db_apps:
            return "alternate"
        return None

    def db_for_write(self, model, **hints):
        """Return the alternate db for write operations."""
        if model._meta.app_label in self.alternate_db_apps:
            return "alternate"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both models are in the alternate db."""
        if (
            obj1._meta.app_label in self.alternate_db_apps
            and obj2._meta.app_label in self.alternate_db_apps
        ):
            return True
        return None
