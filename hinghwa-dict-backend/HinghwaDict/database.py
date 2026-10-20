"""SQLite path configuration; directory binds must include journals/sidecars."""

import os

from django.core.exceptions import ImproperlyConfigured


def sqlite_database_path(configured, base_dir):
    if not configured:
        return os.path.join(base_dir, "db.sqlite3")
    if not os.path.isabs(configured):
        raise ImproperlyConfigured("SQLITE_DATABASE_PATH must be an absolute path")
    return os.path.realpath(configured)
