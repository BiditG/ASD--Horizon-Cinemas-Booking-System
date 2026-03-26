"""
tests/test_booking_manager.py
=============================
Pytest suite for the HCBS Booking Manager permission checks.
"""

import sqlite3
import pytest
from src.models.booking import BookingManager
import src.database.db_connection as db_conn

@pytest.fixture
def memory_db(monkeypatch):
    """Create an in-memory SQLite database populated with minimal schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None  # Allow explicit BEGIN
    
    # Mock get_connection to return our memory DB where it's imported
    monkeypatch.setattr("src.models.showing.get_connection", lambda: conn)
    monkeypatch.setattr("src.database.db_connection.get_connection", lambda: conn)
    
    conn.executescript(
        """
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cinema_id INTEGER,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL,
            theme_pref TEXT NOT NULL DEFAULT 'dark',
            is_active INTEGER NOT NULL DEFAULT 1,
            last_login TEXT
        );
        CREATE TABLE cinemas (
            cinema_id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id INTEGER,
            cinema_name TEXT
        );
        CREATE TABLE screens (
            screen_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cinema_id INTEGER,
            total_capacity INTEGER
        );
        CREATE TABLE showings (
            showing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_id INTEGER,
            screen_id INTEGER,
            show_date TEXT,
            show_time TEXT,
            show_type TEXT,
            seats_remaining INTEGER,
            is_cancelled INTEGER DEFAULT 0
        );
        CREATE TABLE bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            showing_id INTEGER,
            booking_ref TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            total_cost REAL NOT NULL,
            booking_status TEXT NOT NULL,
            booked_by_agent BOOLEAN NOT NULL
        );
        CREATE TABLE tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            seat_number TEXT NOT NULL,
            ticket_type TEXT NOT NULL,
            unit_price REAL NOT NULL
        );
        """
    )
    
    # Insert dummy cinemas
    conn.execute("INSERT INTO cinemas (cinema_name) VALUES ('Cinema A'), ('Cinema B')")
    
    # Insert dummy users: staff (cinema 1), admin (cinema 1)
    conn.execute("INSERT INTO users (cinema_id, username, password_hash, full_name, email, role) VALUES (1, 'staff_a', 'hash', 'Staff A', 'a@a.com', 'staff')")
    conn.execute("INSERT INTO users (cinema_id, username, password_hash, full_name, email, role) VALUES (1, 'admin_u', 'hash', 'Admin', 'admin@a.com', 'admin')")
    
    # Insert screens (screen 1 in cinema 1, screen 2 in cinema 2)
    conn.execute("INSERT INTO screens (cinema_id, total_capacity) VALUES (1, 100)")
    conn.execute("INSERT INTO screens (cinema_id, total_capacity) VALUES (2, 100)")
    
    # Insert showings (showing 1 in cinema 1, showing 2 in cinema 2)
    conn.execute("INSERT INTO showings (screen_id, seats_remaining, is_cancelled) VALUES (1, 100, 0)")
    conn.execute("INSERT INTO showings (screen_id, seats_remaining, is_cancelled) VALUES (2, 100, 0)")
    
    yield conn
    conn.close()

def test_staff_booking_home_cinema(memory_db):
    """Staff at Cinema 1 booking Showing 1 (Cinema 1). Should succeed."""
    res = BookingManager.create_booking(
        showing_id=1, staff_user_id=1, ticket_type="lower_hall", quantity=1, 
        customer_name="Test", customer_email="", customer_phone="", unit_price=10.0, 
        db_connection=memory_db
    )
    assert res["booking_ref"].startswith("HCBS-")
    assert memory_db.execute("SELECT seats_remaining FROM showings WHERE showing_id=1").fetchone()[0] == 99

def test_staff_booking_other_cinema(memory_db):
    """Staff at Cinema 1 booking Showing 2 (Cinema 2). Should raise PermissionError."""
    with pytest.raises(PermissionError, match="Staff can only book at their home cinema"):
        BookingManager.create_booking(
            showing_id=2, staff_user_id=1, ticket_type="lower_hall", quantity=1, 
            customer_name="Test", customer_email="", customer_phone="", unit_price=10.0, 
            db_connection=memory_db
        )

def test_admin_booking_other_cinema(memory_db):
    """Admin at Cinema 1 booking Showing 2 (Cinema 2). Should succeed."""
    res = BookingManager.create_booking(
        showing_id=2, staff_user_id=2, ticket_type="lower_hall", quantity=1, 
        customer_name="Test", customer_email="", customer_phone="", unit_price=10.0, 
        db_connection=memory_db
    )
    assert res["booking_ref"].startswith("HCBS-")
    assert memory_db.execute("SELECT seats_remaining FROM showings WHERE showing_id=2").fetchone()[0] == 99
