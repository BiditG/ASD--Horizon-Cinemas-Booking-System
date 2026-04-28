"""
src/database/db_connection.py
==============================
Shared database connection module for HCBS.

All model classes import get_connection() from here to ensure every
part of the application shares the same SQLite connection that is
managed by the SessionManager singleton.
"""

import sqlite3
import os
from typing import Optional

from src.database.schema_migrate import apply_migrations

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, '..', '..'))
DB_PATH = os.path.join(_PROJECT_ROOT, 'hcbs.db')

_connection: Optional[sqlite3.Connection] = None


def get_connection() -> sqlite3.Connection:
    """
    Return the shared SQLite connection, creating it if necessary.

    The connection uses ``check_same_thread=False`` to allow the GUI's
    background authentication thread to reuse it safely (reads only
    during auth). Row factory is set to ``sqlite3.Row`` so columns can
    be accessed by name.

    Returns:
        sqlite3.Connection: The active database connection.
    """
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA foreign_keys = ON")
        apply_migrations(_connection)
    return _connection


def close_connection() -> None:
    """Close and reset the shared connection (called on app exit)."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
