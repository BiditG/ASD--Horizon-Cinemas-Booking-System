"""
src/models/cinema.py
====================
Cinema model for the Horizon Cinemas Booking System (HCBS).

Maps to the `cinemas` table in the SQLite database and provides
CRUD operations used by the Manager and Admin GUI windows.
"""

import sqlite3
from typing import Optional
from src.database.db_connection import get_connection


class CinemaNotFoundError(Exception):
    """Raised when a cinema lookup returns no result."""


class Cinema:
    """
    Represents a single Horizon Cinemas venue.

    Attributes:
        cinema_id  (int):           Primary key.
        city_id    (int):           FK → cities.city_id.
        cinema_name(str):           Display name of the cinema.
        location   (str):           Street address / location string.
        is_active  (bool):          Whether the cinema is currently operating.
    """

    def __init__(
        self,
        cinema_id: int,
        city_id: int,
        cinema_name: str,
        location: str = "",
        is_active: bool = True,
    ) -> None:
        self.cinema_id: int   = cinema_id
        self.city_id: int     = city_id
        self.cinema_name: str = cinema_name
        self.location: str    = location
        self.is_active: bool  = bool(is_active)

    # ------------------------------------------------------------------
    # Factory helper
    # ------------------------------------------------------------------

    @classmethod
    def _from_row(cls, row: sqlite3.Row) -> "Cinema":
        """Construct a Cinema from a sqlite3.Row object."""
        return cls(
            cinema_id   = row["cinema_id"],
            city_id     = row["city_id"],
            cinema_name = row["cinema_name"],
            location    = row["location"] if "location" in row.keys() else "",
            is_active   = row["is_active"] if "is_active" in row.keys() else True,
        )

    @staticmethod
    def _table_columns(conn: sqlite3.Connection) -> set[str]:
        return {row[1] for row in conn.execute("PRAGMA table_info(cinemas)").fetchall()}

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @staticmethod
    def get_all() -> list["Cinema"]:
        """
        Retrieve all active cinemas from the database.

        Returns:
            list[Cinema]: All rows where is_active = 1, ordered by city then name.

        Raises:
            sqlite3.DatabaseError: On any database-level error.
        """
        try:
            conn   = get_connection()
            columns = Cinema._table_columns(conn)
            if "is_active" in columns:
                cursor = conn.execute(
                    "SELECT * FROM cinemas WHERE is_active = 1 ORDER BY city_id, cinema_name"
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM cinemas ORDER BY city_id, cinema_name"
                )
            return [Cinema._from_row(row) for row in cursor.fetchall()]
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Cinema.get_all failed: {exc}") from exc

    @staticmethod
    def get_by_id(cinema_id: int) -> "Cinema":
        """
        Retrieve a single cinema by its primary key.

        Args:
            cinema_id (int): The cinema's primary key.

        Returns:
            Cinema: The matching Cinema object.

        Raises:
            CinemaNotFoundError: If no cinema with that ID exists.
            sqlite3.DatabaseError: On any database-level error.
        """
        try:
            conn   = get_connection()
            cursor = conn.execute(
                "SELECT * FROM cinemas WHERE cinema_id = ?", (cinema_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise CinemaNotFoundError(f"No cinema found with id={cinema_id}.")
            return Cinema._from_row(row)
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Cinema.get_by_id failed: {exc}") from exc

    @staticmethod
    def get_by_city(city_id: int) -> list["Cinema"]:
        """
        Retrieve all active cinemas in a given city.

        Args:
            city_id (int): FK to the cities table.

        Returns:
            list[Cinema]: All active cinemas for that city.

        Raises:
            sqlite3.DatabaseError: On any database-level error.
        """
        try:
            conn   = get_connection()
            columns = Cinema._table_columns(conn)
            if "is_active" in columns:
                cursor = conn.execute(
                    "SELECT * FROM cinemas WHERE city_id = ? AND is_active = 1",
                    (city_id,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM cinemas WHERE city_id = ?",
                    (city_id,)
                )
            return [Cinema._from_row(row) for row in cursor.fetchall()]
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Cinema.get_by_city failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    @staticmethod
    def create(city_id: int, name: str, location: str) -> "Cinema":
        """
        Insert a new cinema record and return the created Cinema object.

        Args:
            city_id  (int): FK to the cities table.
            name     (str): Cinema display name.
            location (str): Street address / venue location.

        Returns:
            Cinema: The newly created Cinema, with its assigned cinema_id.

        Raises:
            ValueError: If name or location are empty strings.
            sqlite3.DatabaseError: On any database-level error.
        """
        if not name.strip():
            raise ValueError("Cinema name cannot be empty.")
        if not location.strip():
            raise ValueError("Cinema location cannot be empty.")
        try:
            conn   = get_connection()
            columns = Cinema._table_columns(conn)
            if "location" in columns and "is_active" in columns:
                cursor = conn.execute(
                    """
                    INSERT INTO cinemas (city_id, cinema_name, location, is_active)
                    VALUES (?, ?, ?, 1)
                    """,
                    (city_id, name.strip(), location.strip())
                )
            elif "location" in columns:
                cursor = conn.execute(
                    "INSERT INTO cinemas (city_id, cinema_name, location) VALUES (?, ?, ?)",
                    (city_id, name.strip(), location.strip())
                )
            else:
                cursor = conn.execute(
                    "INSERT INTO cinemas (city_id, cinema_name) VALUES (?, ?)",
                    (city_id, name.strip())
                )
            conn.commit()
            return Cinema(
                cinema_id   = cursor.lastrowid,
                city_id     = city_id,
                cinema_name = name.strip(),
                location    = location.strip(),
                is_active   = True
            )
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Cinema.create failed: {exc}") from exc

    @staticmethod
    def update(cinema_id: int, name: str, location: str) -> bool:
        """
        Update the name and location of an existing cinema.

        Args:
            cinema_id (int): PK of the cinema to update.
            name      (str): New display name.
            location  (str): New location string.

        Returns:
            bool: True if a row was updated, False if no matching ID was found.

        Raises:
            ValueError: If name or location are empty strings.
            sqlite3.DatabaseError: On any database-level error.
        """
        if not name.strip():
            raise ValueError("Cinema name cannot be empty.")
        try:
            conn   = get_connection()
            columns = Cinema._table_columns(conn)
            if "location" in columns:
                cursor = conn.execute(
                    "UPDATE cinemas SET cinema_name = ?, location = ? WHERE cinema_id = ?",
                    (name.strip(), location.strip(), cinema_id)
                )
            else:
                cursor = conn.execute(
                    "UPDATE cinemas SET cinema_name = ? WHERE cinema_id = ?",
                    (name.strip(), cinema_id)
                )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Cinema.update failed: {exc}") from exc

    @staticmethod
    def deactivate(cinema_id: int) -> bool:
        """
        Soft-delete a cinema by setting is_active = 0.

        Args:
            cinema_id (int): PK of the cinema to deactivate.

        Returns:
            bool: True if a row was updated, False if not found.

        Raises:
            sqlite3.DatabaseError: On any database-level error.
        """
        try:
            conn   = get_connection()
            columns = Cinema._table_columns(conn)
            if "is_active" not in columns:
                return False
            cursor = conn.execute(
                "UPDATE cinemas SET is_active = 0 WHERE cinema_id = ?",
                (cinema_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Cinema.deactivate failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Cinema(id={self.cinema_id}, name={self.cinema_name!r}, "
            f"city_id={self.city_id}, active={self.is_active})"
        )

    def __str__(self) -> str:
        return self.cinema_name
