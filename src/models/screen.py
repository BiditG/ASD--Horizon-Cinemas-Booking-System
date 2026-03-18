"""
src/models/screen.py
====================
Screen model for the Horizon Cinemas Booking System (HCBS).

Maps to the `screens` table and provides read operations
used by Admin and Booking Staff GUI windows when selecting seats.
"""

import sqlite3
from typing import Optional
from src.database.db_connection import get_connection


class ScreenNotFoundError(Exception):
    """Raised when a screen lookup returns no result."""


class Screen:
    """
    Represents a single screening room inside a cinema.

    Attributes:
        screen_id           (int): Primary key.
        cinema_id           (int): FK → cinemas.cinema_id.
        screen_number       (int): The screen's number within the cinema (1–6).
        total_capacity      (int): Total number of seats (50–120).
        lower_hall_seats    (int): Seats in the lower hall zone (~30% of total).
        upper_gallery_seats (int): Seats in the upper gallery zone.
        vip_seats           (int): VIP seats (up to 10).
    """

    def __init__(
        self,
        screen_id: int,
        cinema_id: int,
        screen_number: int,
        total_capacity: int,
        lower_hall_seats: int,
        upper_gallery_seats: int,
        vip_seats: int,
    ) -> None:
        self.screen_id:           int = screen_id
        self.cinema_id:           int = cinema_id
        self.screen_number:       int = screen_number
        self.total_capacity:      int = total_capacity
        self.lower_hall_seats:    int = lower_hall_seats
        self.upper_gallery_seats: int = upper_gallery_seats
        self.vip_seats:           int = vip_seats

    # ------------------------------------------------------------------
    # Factory helper
    # ------------------------------------------------------------------

    @classmethod
    def _from_row(cls, row: sqlite3.Row) -> "Screen":
        """Construct a Screen from a sqlite3.Row object."""
        return cls(
            screen_id           = row["screen_id"],
            cinema_id           = row["cinema_id"],
            screen_number       = row["screen_number"],
            total_capacity      = row["total_capacity"],
            lower_hall_seats    = row["lower_hall_seats"],
            upper_gallery_seats = row["upper_gallery_seats"],
            vip_seats           = row["vip_seats"],
        )

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @staticmethod
    def get_by_cinema(cinema_id: int) -> list["Screen"]:
        """
        Retrieve all screens belonging to a given cinema.

        Args:
            cinema_id (int): FK to the cinemas table.

        Returns:
            list[Screen]: All screens for that cinema, ordered by screen_number.

        Raises:
            sqlite3.DatabaseError: On any database-level error.
        """
        try:
            conn   = get_connection()
            cursor = conn.execute(
                "SELECT * FROM screens WHERE cinema_id = ? ORDER BY screen_number",
                (cinema_id,)
            )
            return [Screen._from_row(row) for row in cursor.fetchall()]
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Screen.get_by_cinema failed: {exc}") from exc

    @staticmethod
    def get_by_id(screen_id: int) -> "Screen":
        """
        Retrieve a single screen by its primary key.

        Args:
            screen_id (int): The screen's primary key.

        Returns:
            Screen: The matching Screen object.

        Raises:
            ScreenNotFoundError: If no screen with that ID exists.
            sqlite3.DatabaseError: On any database-level error.
        """
        try:
            conn   = get_connection()
            cursor = conn.execute(
                "SELECT * FROM screens WHERE screen_id = ?", (screen_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise ScreenNotFoundError(f"No screen found with id={screen_id}.")
            return Screen._from_row(row)
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Screen.get_by_id failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def zone_summary(self) -> str:
        """Human-readable breakdown of seat zones for display in the GUI."""
        return (
            f"Lower Hall: {self.lower_hall_seats} | "
            f"Upper Gallery: {self.upper_gallery_seats} | "
            f"VIP: {self.vip_seats}"
        )

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Screen(id={self.screen_id}, cinema_id={self.cinema_id}, "
            f"number={self.screen_number}, capacity={self.total_capacity})"
        )

    def __str__(self) -> str:
        return f"Screen {self.screen_number} (capacity: {self.total_capacity})"
