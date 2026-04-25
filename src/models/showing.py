"""
src/models/showing.py
=====================
Showing model for the Horizon Cinemas Booking System (HCBS).

Maps to the `showings` table and provides read/write operations
used by Booking Staff and Admin GUI windows.
"""

import sqlite3
import datetime
from typing import Optional
from src.database.db_connection import get_connection


class ShowingNotFoundError(Exception):
    """Raised when a showing lookup returns no result."""


class ShowingFullError(Exception):
    """Raised when a booking is attempted on a fully booked showing."""


class Showing:
    """
    Represents a scheduled movie screening at a specific screen.

    Attributes:
        showing_id      (int):  Primary key.
        cinema_id       (int):  FK → cinemas.cinema_id (denormalised for fast lookup).
        screen_id       (int):  FK → screens.screen_id.
        film_id         (int):  FK → films.film_id.
        show_date       (str):  ISO date string (YYYY-MM-DD).
        show_time       (str):  Time string (HH:MM).
        show_type       (str):  One of 'morning', 'afternoon', 'evening'.
        seats_remaining (int):  Running count of unsold seats.
        is_cancelled    (bool): True if the showing has been cancelled.
    """

    VALID_SHOW_TYPES = ('morning', 'afternoon', 'evening')
    SHOW_TYPE_TIMES  = {'morning': '10:00', 'afternoon': '14:30', 'evening': '19:00'}

    def __init__(self, showing_id: int, cinema_id: int, screen_id: int,
                 film_id: int, show_date: str, show_time: str,
                 show_type: str, seats_remaining: int, is_cancelled: bool = False):
        self.showing_id:       int  = showing_id
        self.cinema_id:        int  = cinema_id
        self.screen_id:        int  = screen_id
        self.film_id:          int  = film_id
        self.show_date:        str  = show_date
        self.show_time:        str  = show_time
        self.show_type:        str  = show_type
        self.seats_remaining:  int  = seats_remaining
        self.is_cancelled:     bool = bool(is_cancelled)

    # ------------------------------------------------------------------
    # Factory helper
    # ------------------------------------------------------------------

    @classmethod
    def _from_row(cls, row: sqlite3.Row) -> "Showing":
        """Construct a Showing from a sqlite3.Row object."""
        keys = row.keys()
        return cls(
            showing_id      = row["showing_id"],
            cinema_id       = row["cinema_id"]   if "cinema_id"   in keys else 0,
            screen_id       = row["screen_id"],
            film_id         = row["film_id"],
            show_date       = row["show_date"],
            show_time       = row["show_time"],
            show_type       = row["show_type"],
            seats_remaining = row["seats_remaining"],
            is_cancelled    = row["is_cancelled"] if "is_cancelled" in keys else False,
        )

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @staticmethod
    def get_by_cinema_date(cinema_id: int, date: str) -> list["Showing"]:
        """
        Retrieve all non-cancelled showings for a cinema on a given date.

        The query joins through the screens table to filter by cinema_id,
        since the showings table stores screen_id not cinema_id directly.

        Args:
            cinema_id (int): FK to the cinemas table.
            date      (str): ISO date string 'YYYY-MM-DD'.

        Returns:
            list[Showing]: Showings ordered by show_time ascending.

        Raises:
            sqlite3.DatabaseError: On any database-level error.
        """
        try:
            conn   = get_connection()
            cursor = conn.execute(
                """
                SELECT s.*, sc.cinema_id
                FROM   showings s
                JOIN   screens  sc ON s.screen_id = sc.screen_id
                WHERE  sc.cinema_id = ?
                AND    s.show_date  = ?
                AND    s.is_cancelled = 0
                ORDER BY s.show_time
                """,
                (cinema_id, date)
            )
            return [Showing._from_row(row) for row in cursor.fetchall()]
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(
                f"Showing.get_by_cinema_date failed: {exc}"
            ) from exc

    @staticmethod
    def get_by_id(showing_id: int) -> "Showing":
        """
        Retrieve a single showing by its primary key.

        Args:
            showing_id (int): The showing's primary key.

        Returns:
            Showing: The matching Showing object.

        Raises:
            ShowingNotFoundError: If no showing with that ID exists.
            sqlite3.DatabaseError: On any database-level error.
        """
        try:
            conn   = get_connection()
            cursor = conn.execute(
                """
                SELECT s.*, sc.cinema_id
                FROM   showings s
                JOIN   screens  sc ON s.screen_id = sc.screen_id
                WHERE  s.showing_id = ?
                """,
                (showing_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise ShowingNotFoundError(
                    f"No showing found with id={showing_id}."
                )
            return Showing._from_row(row)
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(
                f"Showing.get_by_id failed: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Availability checks
    # ------------------------------------------------------------------

    @staticmethod
    def is_available(showing_id: int, qty: int) -> bool:
        """
        Check whether a showing has enough seats for the requested quantity.

        Args:
            showing_id (int): The showing to check.
            qty        (int): Number of seats requested.

        Returns:
            bool: True if seats_remaining >= qty and showing is not cancelled.

        Raises:
            ShowingNotFoundError: If no showing with that ID exists.
            sqlite3.DatabaseError: On any database-level error.
        """
        showing = Showing.get_by_id(showing_id)
        if showing.is_cancelled:
            return False
        return showing.seats_remaining >= qty

    @staticmethod
    def get_live_availability(showing_id: int, ticket_type: str) -> int:
        """
        Returns the real-time number of available seats for a specific ticket type
        by checking the screen capacity and subtracting active bookings.

        Args:
            showing_id (int): The showing to check.
            ticket_type (str): 'lower_hall', 'upper_gallery', or 'vip'.

        Returns:
            int: Number of available seats for this type.
        """
        try:
            conn = get_connection()
            col_name = f"{ticket_type}_seats"
            
            # Prevent SQL injection by checking against known valid types
            if ticket_type not in ('lower_hall', 'upper_gallery', 'vip'):
                raise ValueError(f"Invalid ticket_type '{ticket_type}'")
                
            row = conn.execute(f"""
                SELECT sc.{col_name} as capacity
                FROM screens sc
                JOIN showings s ON sc.screen_id = s.screen_id
                WHERE s.showing_id = ?
            """, (showing_id,)).fetchone()
            
            if not row:
                raise ValueError(f"Showing {showing_id} not found.")
                
            capacity = row["capacity"]
            
            count_row = conn.execute("""
                SELECT COUNT(t.ticket_id) as booked
                FROM tickets t
                JOIN bookings b ON t.booking_id = b.booking_id
                WHERE b.showing_id = ? 
                AND t.ticket_type = ? 
                AND b.booking_status = 'Active'
            """, (showing_id, ticket_type)).fetchone()
            
            booked = count_row["booked"] if count_row else 0
            
            return max(0, capacity - booked)
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Showing.get_live_availability failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Seat count mutations (called inside a booking transaction)
    # ------------------------------------------------------------------

    @staticmethod
    def decrement_seats(showing_id: int, qty: int) -> bool:
        """
        Reduce seats_remaining by qty (called when a booking is confirmed).

        Args:
            showing_id (int): The showing to update.
            qty        (int): Number of seats to reserve.

        Returns:
            bool: True if the update succeeded, False if showing not found.

        Raises:
            ShowingFullError: If seats_remaining < qty (prevents over-booking).
            sqlite3.DatabaseError: On any database-level error.
        """
        try:
            conn = get_connection()
            # Atomic check-and-update to prevent race conditions
            cursor = conn.execute(
                """
                UPDATE showings
                SET    seats_remaining = seats_remaining - ?
                WHERE  showing_id = ?
                AND    seats_remaining >= ?
                """,
                (qty, showing_id, qty)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise ShowingFullError(
                    f"Showing {showing_id} does not have {qty} seat(s) available."
                )
            return True
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(
                f"Showing.decrement_seats failed: {exc}"
            ) from exc

    @staticmethod
    def increment_seats(showing_id: int, qty: int) -> bool:
        """
        Increase seats_remaining by qty (called when a booking is cancelled).

        Args:
            showing_id (int): The showing to update.
            qty        (int): Number of seats to release.

        Returns:
            bool: True if a row was updated, False if showing not found.

        Raises:
            sqlite3.DatabaseError: On any database-level error.
        """
        try:
            conn   = get_connection()
            cursor = conn.execute(
                """
                UPDATE showings
                SET    seats_remaining = seats_remaining + ?
                WHERE  showing_id = ?
                """,
                (qty, showing_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(
                f"Showing.increment_seats failed: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    @staticmethod
    def create(cinema_id: int, screen_id: int, film_id: int,
               date: str, show_type: str) -> "Showing":
        """
        Insert a new showing and return the created Showing object.

        The show_time is automatically derived from the show_type using the
        SHOW_TYPE_TIMES mapping. seats_remaining is initialised to the
        screen's total_capacity.

        Args:
            cinema_id (int): FK to cinemas (used to validate the screen belongs to it).
            screen_id (int): FK to screens.
            film_id   (int): FK to films.
            date      (str): ISO date string 'YYYY-MM-DD'.
            show_type (str): One of 'morning', 'afternoon', 'evening'.

        Returns:
            Showing: The newly created Showing object with its showing_id.

        Raises:
            ValueError: If show_type is invalid or date is in the past.
            sqlite3.DatabaseError: On any database-level error.
        """
        if show_type not in Showing.VALID_SHOW_TYPES:
            raise ValueError(
                f"Invalid show_type '{show_type}'. "
                f"Must be one of: {', '.join(Showing.VALID_SHOW_TYPES)}"
            )
        try:
            show_date_obj = datetime.date.fromisoformat(date)
        except ValueError:
            raise ValueError(f"Invalid date format '{date}'. Expected YYYY-MM-DD.")

        if show_date_obj < datetime.date.today():
            raise ValueError("Cannot schedule a showing in the past.")

        try:
            conn = get_connection()

            # Fetch screen capacity for seats_remaining initialisation
            row = conn.execute(
                "SELECT total_capacity FROM screens WHERE screen_id = ?",
                (screen_id,)
            ).fetchone()
            if row is None:
                raise ValueError(f"No screen found with screen_id={screen_id}.")

            capacity  = row["total_capacity"]
            show_time = Showing.SHOW_TYPE_TIMES[show_type]
            
            # Check for overlaps
            overlap = conn.execute(
                "SELECT showing_id FROM showings WHERE screen_id = ? AND show_date = ? AND show_time = ?",
                (screen_id, date, show_time)
            ).fetchone()
            if overlap:
                raise Exception(f"Overlapping showing exists on screen {screen_id} at {date} {show_time}")

            cursor = conn.execute(
                """
                INSERT INTO showings
                    (film_id, screen_id, show_date, show_time,
                     show_type, seats_remaining)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (film_id, screen_id, date, show_time, show_type, capacity)
            )
            conn.commit()
            return Showing(
                showing_id      = cursor.lastrowid,
                cinema_id       = cinema_id,
                screen_id       = screen_id,
                film_id         = film_id,
                show_date       = date,
                show_time       = show_time,
                show_type       = show_type,
                seats_remaining = capacity,
                is_cancelled    = False,
            )
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Showing.create failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def datetime_display(self) -> str:
        """Return a formatted date-time string for GUI display."""
        return f"{self.show_date} at {self.show_time} ({self.show_type.capitalize()})"

    @property
    def is_sold_out(self) -> bool:
        """True when no seats remain."""
        return self.seats_remaining <= 0

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """
        Mark this showing instance as cancelled in the database.
        Note: This is a convenience method; prefer CancellationManager.cancel_showing
        if you need to handle bookings as well.
        """
        try:
            conn = get_connection()
            conn.execute("UPDATE showings SET is_cancelled = 1 WHERE showing_id = ?", (self.showing_id,))
            conn.commit()
            self.is_cancelled = True
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Showing.cancel failed: {exc}") from exc

    def __repr__(self) -> str:
        return (
            f"Showing(id={self.showing_id}, film_id={self.film_id}, "
            f"screen_id={self.screen_id}, date={self.show_date!r}, "
            f"type={self.show_type!r}, seats={self.seats_remaining}, cancelled={self.is_cancelled})"
        )

    def __str__(self) -> str:
        return f"{self.datetime_display}{' [CANCELLED]' if self.is_cancelled else ''}"
