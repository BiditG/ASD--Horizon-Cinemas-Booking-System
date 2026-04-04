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
            customer_email TEXT DEFAULT '',
            total_cost REAL NOT NULL,
            booking_status TEXT NOT NULL,
            booked_by_agent BOOLEAN NOT NULL,
            cancellation_fee REAL DEFAULT 0.00,
            cancelled_at TEXT,
            staff_id INTEGER DEFAULT 1,
            booking_time TEXT DEFAULT CURRENT_TIMESTAMP
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
    
    import datetime
    today_str = datetime.date.today().isoformat()
    # Insert showings (showing 1 in cinema 1, showing 2 in cinema 2)
    conn.execute(f"INSERT INTO showings (screen_id, show_date, seats_remaining, is_cancelled) VALUES (1, '{today_str}', 100, 0)")
    conn.execute(f"INSERT INTO showings (screen_id, show_date, seats_remaining, is_cancelled) VALUES (2, '{today_str}', 100, 0)")
    
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

def test_validate_booking_date_past():
    """Test date validation for past date."""
    from src.models.booking import BookingManager, BookingError
    import datetime
    past_date = datetime.date.today() - datetime.timedelta(days=1)
    with pytest.raises(BookingError, match='Cannot book for a past showing'):
        BookingManager.validate_booking_date(past_date)

def test_validate_booking_date_valid():
    """Test date validation for valid date."""
    from src.models.booking import BookingManager
    import datetime
    
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
            customer_email TEXT DEFAULT '',
            total_cost REAL NOT NULL,
            booking_status TEXT NOT NULL,
            booked_by_agent BOOLEAN NOT NULL,
            cancellation_fee REAL DEFAULT 0.00,
            cancelled_at TEXT,
            staff_id INTEGER DEFAULT 1,
            booking_time TEXT DEFAULT CURRENT_TIMESTAMP
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
    
    import datetime
    today_str = datetime.date.today().isoformat()
    # Insert showings (showing 1 in cinema 1, showing 2 in cinema 2)
    conn.execute(f"INSERT INTO showings (screen_id, show_date, seats_remaining, is_cancelled) VALUES (1, '{today_str}', 100, 0)")
    conn.execute(f"INSERT INTO showings (screen_id, show_date, seats_remaining, is_cancelled) VALUES (2, '{today_str}', 100, 0)")
    
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

def test_validate_booking_date_past():
    """Test date validation for past date."""
    from src.models.booking import BookingManager, BookingError
    import datetime
    past_date = datetime.date.today() - datetime.timedelta(days=1)
    with pytest.raises(BookingError, match='Cannot book for a past showing'):
        BookingManager.validate_booking_date(past_date)

def test_validate_booking_date_valid():
    """Test date validation for valid date."""
    from src.models.booking import BookingManager
    import datetime
    
    # Today should be valid
    today = datetime.date.today()
    assert BookingManager.validate_booking_date(today) is None
    
    # 7 days from today should be valid
    future_7_days = today + datetime.timedelta(days=7)
    assert BookingManager.validate_booking_date(future_7_days) is None

def test_validate_booking_date_future():
    """Test date validation for date too far in future."""
    from src.models.booking import BookingManager, BookingError
    import datetime
    future_date = datetime.date.today() + datetime.timedelta(days=8)
    with pytest.raises(BookingError, match='Advance booking limit is 7 days'):
        BookingManager.validate_booking_date(future_date)

def test_duplicate_booking(memory_db):
    """Test that a duplicate booking by the same email for the same film on the same date is detected."""
    import datetime
    from src.models.booking import BookingManager
    
    today = datetime.date.today().isoformat()
    # Insert a showing for today
    memory_db.execute("INSERT INTO showings (film_id, screen_id, show_date, show_time, show_type, seats_remaining) VALUES (1, 1, ?, '18:00', 'evening', 100)", (today,))
    showing_id = memory_db.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    # Create first booking
    res1 = BookingManager.create_booking(
        showing_id=showing_id, staff_user_id=1, ticket_type="lower_hall", quantity=1,
        customer_name="John Doe", customer_email="john@example.com", customer_phone="", 
        unit_price=10.0, db_connection=memory_db
    )
    
    # Check for duplicate
    dup = BookingManager.check_duplicate("john@example.com", 1, datetime.date.today(), memory_db)
    assert dup is not None
    assert dup["booking_ref"] == res1["booking_ref"]
    
    # Check for non-duplicate
    no_dup = BookingManager.check_duplicate("jane@example.com", 1, datetime.date.today(), memory_db)
    assert no_dup is None
