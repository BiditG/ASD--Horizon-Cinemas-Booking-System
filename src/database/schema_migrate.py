"""
Lightweight idempotent migrations for existing SQLite databases.

Fresh installs use setup_db.py CREATE TABLE definitions; this module adds
columns that older hcbs.db files may be missing so models stay in sync.
"""

import sqlite3


def migrate_films(conn: sqlite3.Connection) -> None:
    """Ensure ``films`` has columns expected by :class:`Film`."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='films'"
    ).fetchone()
    if not row:
        return
    existing = {r[1] for r in conn.execute("PRAGMA table_info(films)").fetchall()}
    alters: list[str] = []
    if "description" not in existing:
        alters.append("ALTER TABLE films ADD COLUMN description TEXT DEFAULT ''")
    if "imdb_rating" not in existing:
        alters.append("ALTER TABLE films ADD COLUMN imdb_rating REAL")
    if "cast_members" not in existing:
        alters.append("ALTER TABLE films ADD COLUMN cast_members TEXT DEFAULT ''")
    if "poster_path" not in existing:
        alters.append("ALTER TABLE films ADD COLUMN poster_path TEXT DEFAULT ''")
    if "is_active" not in existing:
        alters.append(
            "ALTER TABLE films ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1"
        )
    for sql in alters:
        conn.execute(sql)


def apply_migrations(conn: sqlite3.Connection) -> None:
    migrate_films(conn)
    conn.commit()
