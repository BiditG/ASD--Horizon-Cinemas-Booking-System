"""
src/models/film.py
==================
Film model for the Horizon Cinemas Booking System (HCBS).

Maps to the `films` table and provides full CRUD operations.
"""

import sqlite3
from typing import Optional
from src.database.db_connection import get_connection


class FilmNotFoundError(Exception):
    """Raised when a film lookup returns no result."""


class Film:
    """
    Represents a movie available for scheduling at Horizon Cinemas.

    Attributes:
        film_id       (int):            Primary key.
        title         (str):            Movie title.
        description   (str):            Plot synopsis.
        genre         (str):            Genre string.
        age_rating    (str):            BBFC age rating.
        duration_mins (int):            Runtime in minutes.
        imdb_rating   (Optional[float]):IMDb score out of 10.
        cast_members  (str):            Comma-separated cast list.
        poster_path   (str):            Relative path to poster image asset.
        is_active     (bool):           False when removed from circulation.
    """

    VALID_RATINGS = ('U', 'PG', '12', '12A', '15', '18', 'R')

    def __init__(self, film_id, title, description="", genre="", age_rating="PG",
                 duration_mins=0, imdb_rating=None, cast_members="",
                 poster_path="", is_active=True):
        self.film_id       = film_id
        self.title         = title
        self.description   = description
        self.genre         = genre
        self.age_rating    = age_rating
        self.duration_mins = duration_mins
        self.imdb_rating   = imdb_rating
        self.cast_members  = cast_members
        self.poster_path   = poster_path
        self.is_active     = bool(is_active)

    @classmethod
    def _from_row(cls, row: sqlite3.Row) -> "Film":
        keys = row.keys()
        return cls(
            film_id       = row["film_id"],
            title         = row["title"],
            description   = row["description"]   if "description"   in keys else "",
            genre         = row["genre"]          if "genre"         in keys else "",
            age_rating    = row["age_rating"]     if "age_rating"    in keys else "PG",
            duration_mins = row["duration_mins"]  if "duration_mins" in keys else 0,
            imdb_rating   = row["imdb_rating"]    if "imdb_rating"   in keys else None,
            cast_members  = row["cast_members"]   if "cast_members"  in keys else "",
            poster_path   = row["poster_path"]    if "poster_path"   in keys else "",
            is_active     = row["is_active"]      if "is_active"     in keys else True,
        )

    @staticmethod
    def get_all_active() -> list["Film"]:
        """Return all active films ordered alphabetically."""
        try:
            cursor = get_connection().execute(
                "SELECT * FROM films WHERE is_active = 1 ORDER BY title"
            )
            return [Film._from_row(r) for r in cursor.fetchall()]
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Film.get_all_active failed: {exc}") from exc

    @staticmethod
    def get_by_id(film_id: int) -> "Film":
        """Return a single film by PK, or raise FilmNotFoundError."""
        try:
            row = get_connection().execute(
                "SELECT * FROM films WHERE film_id = ?", (film_id,)
            ).fetchone()
            if row is None:
                raise FilmNotFoundError(f"No film found with id={film_id}.")
            return Film._from_row(row)
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Film.get_by_id failed: {exc}") from exc

    @staticmethod
    def search(query: str = "", genre: str = "", age_rating: str = "") -> list["Film"]:
        """
        Search active films by optional title keyword, genre, and age rating.

        Args:
            query      (str): Partial title (case-insensitive LIKE).
            genre      (str): Exact genre filter.
            age_rating (str): Exact age rating filter.

        Returns:
            list[Film]: Matching Film objects ordered by title.
        """
        try:
            sql, params = "SELECT * FROM films WHERE is_active = 1", []
            if query.strip():
                sql += " AND title LIKE ?"
                params.append(f"%{query.strip()}%")
            if genre.strip():
                sql += " AND genre = ?"
                params.append(genre.strip())
            if age_rating.strip():
                sql += " AND age_rating = ?"
                params.append(age_rating.strip())
            sql += " ORDER BY title"
            return [Film._from_row(r) for r in get_connection().execute(sql, params).fetchall()]
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Film.search failed: {exc}") from exc

    @staticmethod
    def create(title: str, genre: str, age_rating: str, duration_mins: int,
               description: str = "", cast_members: str = "",
               poster_path: str = "", imdb_rating: Optional[float] = None) -> "Film":
        """
        Insert a new film and return the created Film object.

        Raises:
            ValueError: If title is empty, duration <= 0, or age_rating is invalid.
        """
        if not title.strip():
            raise ValueError("Film title cannot be empty.")
        if duration_mins <= 0:
            raise ValueError("Duration must be greater than 0 minutes.")
        if age_rating not in Film.VALID_RATINGS:
            raise ValueError(f"Invalid age rating '{age_rating}'.")
        try:
            conn   = get_connection()
            cursor = conn.execute(
                """INSERT INTO films (title, description, genre, age_rating,
                   duration_mins, imdb_rating, cast_members, poster_path, is_active)
                   VALUES (?,?,?,?,?,?,?,?,1)""",
                (title.strip(), description, genre, age_rating,
                 duration_mins, imdb_rating, cast_members, poster_path)
            )
            conn.commit()
            return Film(cursor.lastrowid, title.strip(), description, genre,
                        age_rating, duration_mins, imdb_rating, cast_members,
                        poster_path, True)
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Film.create failed: {exc}") from exc

    @staticmethod
    def update(film_id: int, **kwargs) -> bool:
        """
        Update one or more fields of a film. Pass column=value keyword args.

        Raises:
            ValueError: If no fields provided or an invalid column name is used.
        """
        ALLOWED = {'title','description','genre','age_rating',
                   'duration_mins','imdb_rating','cast_members','poster_path'}
        if not kwargs:
            raise ValueError("At least one field must be provided.")
        invalid = set(kwargs) - ALLOWED
        if invalid:
            raise ValueError(f"Invalid field(s): {invalid}")
        try:
            conn    = get_connection()
            setters = ", ".join(f"{col} = ?" for col in kwargs)
            cursor  = conn.execute(
                f"UPDATE films SET {setters} WHERE film_id = ?",
                list(kwargs.values()) + [film_id]
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Film.update failed: {exc}") from exc

    @staticmethod
    def deactivate(film_id: int) -> bool:
        """Soft-delete a film by setting is_active = 0."""
        try:
            conn   = get_connection()
            cursor = conn.execute(
                "UPDATE films SET is_active = 0 WHERE film_id = ?", (film_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(f"Film.deactivate failed: {exc}") from exc

    @property
    def duration_formatted(self) -> str:
        """Return runtime as 'Xh Ym'."""
        hrs  = self.duration_mins // 60
        mins = self.duration_mins % 60
        return f"{hrs}h {mins}m" if hrs else f"{mins}m"

    def __repr__(self) -> str:
        return (f"Film(id={self.film_id}, title={self.title!r}, "
                f"rating={self.age_rating!r}, duration={self.duration_mins})")

    def __str__(self) -> str:
        return f"{self.title} ({self.age_rating}) — {self.duration_formatted}"
