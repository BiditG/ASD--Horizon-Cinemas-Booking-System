import pytest
import sqlite3
import datetime
import sys
from unittest.mock import MagicMock

# Mock bcrypt for isolated test environments
mock_bcrypt = MagicMock()
mock_bcrypt.gensalt.return_value = b'salt'
mock_bcrypt.hashpw.return_value = b'hashed_password'
mock_bcrypt.checkpw.return_value = True
sys.modules['bcrypt'] = mock_bcrypt

from src.database import db_connection
from src.database.setup_db import create_tables
from src.models.showing import Showing
from src.models.film import Film
from src.models.cinema import Cinema
from src.models.booking import BookingManager
from src.models.cancellation import CancellationManager
from src.models.user import User
from src.models.reports import ReportManager
from src.utils.waitlist_manager import init_waitlist_db, join_waitlist, process_waitlist

@pytest.fixture(autouse=True)
def setup_integration_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    db_connection._connection = conn  # Inject early for get_connection() callers
    
    cursor = conn.cursor()
    create_tables(cursor)
    cursor.execute("DROP TABLE IF EXISTS waitlist")
    init_waitlist_db()
    
    # Patch schema
    cursor.executescript("""
        ALTER TABLE cinemas ADD COLUMN location TEXT DEFAULT '';
        ALTER TABLE cinemas ADD COLUMN is_active INTEGER DEFAULT 1;
        ALTER TABLE films ADD COLUMN description TEXT DEFAULT '';
        ALTER TABLE films ADD COLUMN imdb_rating REAL DEFAULT NULL;
        ALTER TABLE films ADD COLUMN cast_members TEXT DEFAULT '';
        ALTER TABLE films ADD COLUMN poster_path TEXT DEFAULT '';
        ALTER TABLE films ADD COLUMN is_active INTEGER DEFAULT 1;
        ALTER TABLE showings ADD COLUMN is_cancelled INTEGER DEFAULT 0;
    """)

    # Setup realistic seed data
    cities = ['London', 'Birmingham', 'Manchester']
    for i, c in enumerate(cities, 1):
        conn.execute("INSERT INTO cities (city_id, city_name) VALUES (?, ?)", (i, c))
        conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (?, 'morning', 10.0, '2025-01-01')", (i,))
        conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (?, 'afternoon', 12.0, '2025-01-01')", (i,))
        conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (?, 'evening', 15.0, '2025-01-01')", (i,))

    # 3 cinemas
    for i in range(1, 4):
        Cinema.create(city_id=i, name=f"Cinema {i}", location=f"Loc {i}")
        # Screen ID matches Cinema ID for simplicity
        conn.execute("INSERT INTO screens (screen_id, cinema_id, screen_number, total_capacity, lower_hall_seats, upper_gallery_seats, vip_seats) VALUES (?, ?, 1, 100, 30, 60, 10)", (i, i))

    # 5 films
    for i in range(1, 6):
        Film.create(title=f"Film {i}", genre="Action", age_rating="12A", duration_mins=120)

    # Showings (10 total to spread across)
    today = datetime.date.today().isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    next_week = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
    dates = [today, tomorrow, next_week]
    
    showing_count = 1
    for cinema_id in range(1, 4):
        for film_id in range(1, 4):
            for show_type in ['morning', 'afternoon', 'evening']:
                if showing_count <= 10:
                    try:
                        Showing.create(cinema_id, cinema_id, film_id, dates[showing_count % 3], show_type)
                        showing_count += 1
                    except Exception:
                        pass # avoid overlaps

    # 5 users of each role
    role_count = 1
    for role in ['admin', 'manager', 'staff']:
        for i in range(1, 6):
            conn.execute(
                "INSERT INTO users (user_id, cinema_id, username, password_hash, full_name, email, role, is_active) VALUES (?, ?, ?, 'hash', ?, ?, ?, 1)",
                (role_count, 1, f"{role}{i}", f"{role} {i}", f"{role}{i}@m.com", role)
            )
            role_count += 1

    conn.commit()
    yield conn
    db_connection._connection = None
    conn.close()


# 1. Full booking flow
def test_full_booking_flow(setup_integration_db):
    conn = setup_integration_db
    user = User.login("staff1", "pass", conn) 
    assert user.role == "staff"
    
    # select film / showing
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    showings = Showing.get_by_cinema_date(1, tomorrow)
    showing = showings[0]
    initial_seats = showing.seats_remaining
    
    booking = BookingManager.create_booking(
        showing_id=showing.showing_id,
        staff_user_id=user.user_id,
        ticket_type='lower_hall',
        quantity=2,
        customer_name='John Flow',
        customer_email='john@flow.com',
        customer_phone='1234',
        unit_price=10.0,
        db_connection=conn
    )
    
    assert "booking_ref" in booking
    assert booking["total_cost"] == 20.0
    
    updated_showing = Showing.get_by_id(showing.showing_id)
    assert updated_showing.seats_remaining == initial_seats - 2


# 2. Full cancellation flow
def test_full_cancellation_flow(setup_integration_db):
    conn = setup_integration_db
    next_week = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
    showings = Showing.get_by_cinema_date(1, next_week)
    showing = showings[0]
    initial_seats = showing.seats_remaining
    
    booking = BookingManager.create_booking(
        showing_id=showing.showing_id,
        staff_user_id=11, # staff
        ticket_type='lower_hall',
        quantity=2,
        customer_name='Cancel Flow',
        customer_email='cancel@flow.com',
        customer_phone='1234',
        unit_price=10.0,
        db_connection=conn
    )
    
    result = CancellationManager.cancel_booking(booking['booking_ref'], conn)
    assert result["cancellation_fee"] == 10.0 # 50% of 20
    
    updated_showing = Showing.get_by_id(showing.showing_id)
    assert updated_showing.seats_remaining == initial_seats
    
    db_booking = BookingManager.get_by_ref(booking['booking_ref'], conn)
    assert db_booking["booking_status"] == "Cancelled"


# 3. Admin listing management: Add listing
def test_admin_add_film_listing(setup_integration_db):
    conn = setup_integration_db
    user = User.login("admin1", "pass", conn)
    assert user.role == "admin"
    
    film = Film.create("New Admin Film", "Sci-Fi", "15", 130)
    assert film.film_id is not None
    
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    conn.execute("INSERT INTO screens (screen_id, cinema_id, screen_number, total_capacity, lower_hall_seats, upper_gallery_seats, vip_seats) VALUES (95, 1, 95, 100, 30, 60, 10)")
    showing = Showing.create(1, 95, film.film_id, tomorrow, 'evening')
    
    showings = Showing.get_by_cinema_date(1, tomorrow)
    found = any(s.showing_id == showing.showing_id for s in showings)
    assert found is True


# 4. Admin listing management: Update time
def test_admin_update_show_time(setup_integration_db):
    conn = setup_integration_db
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    conn.execute("INSERT INTO screens (screen_id, cinema_id, screen_number, total_capacity, lower_hall_seats, upper_gallery_seats, vip_seats) VALUES (98, 1, 98, 100, 30, 60, 10)")
    showing = Showing.create(1, 98, 1, tomorrow, 'morning')
    
    # Admin updates time via DB execution (simulating admin window behavior)
    conn.execute("UPDATE showings SET show_time = ?, show_type = ? WHERE showing_id = ?", ("13:00", "afternoon", showing.showing_id))
    conn.commit()
    
    updated = Showing.get_by_id(showing.showing_id)
    assert updated.show_time == "13:00"


# 5. Admin listing management: Remove listing
def test_admin_remove_listing(setup_integration_db):
    conn = setup_integration_db
    Film.deactivate(1)
    
    conn.execute("UPDATE showings SET is_cancelled=1 WHERE film_id=?", (1,))
    conn.commit()
    
    active_films = Film.get_all_active()
    assert not any(f.film_id == 1 for f in active_films)
    
    showings = conn.execute("SELECT * FROM showings WHERE film_id=1 AND is_cancelled=0").fetchall()
    assert len(showings) == 0


# 6. Manager flow: Add new cinema
def test_manager_add_new_cinema(setup_integration_db):
    conn = setup_integration_db
    cinema = Cinema.create(1, "New Manager Cinema", "Location 123")
    
    for i in range(1, 4):
        conn.execute("INSERT INTO screens (cinema_id, screen_number, total_capacity, lower_hall_seats, upper_gallery_seats, vip_seats) VALUES (?, ?, 100, 30, 60, 10)", (cinema.cinema_id, i))
    conn.commit()
    
    screens = conn.execute("SELECT * FROM screens WHERE cinema_id=?", (cinema.cinema_id,)).fetchall()
    assert len(screens) == 3


# 7. Manager flow: Add cinema to new city
def test_manager_add_new_city_cinema(setup_integration_db):
    conn = setup_integration_db
    conn.execute("INSERT INTO cities (city_name) VALUES (?)", ("Edinburgh",))
    city_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    cinema = Cinema.create(city_id, "Edinburgh Central", "Royal Mile")
    assert cinema.cinema_name == "Edinburgh Central"
    
    fetched = Cinema.get_by_id(cinema.cinema_id)
    assert fetched.city_id == city_id


# 8. Reporting: Monthly revenue report
def test_monthly_revenue_report(setup_integration_db):
    conn = setup_integration_db
    today = datetime.date.today()
    showings = Showing.get_by_cinema_date(1, today.isoformat())
    if not showings:
        # Create a showing if none exists for today due to modulo setup
        conn.execute("INSERT INTO screens (screen_id, cinema_id, screen_number, total_capacity, lower_hall_seats, upper_gallery_seats, vip_seats) VALUES (97, 1, 97, 100, 30, 60, 10)")
        Showing.create(1, 97, 1, today.isoformat(), 'morning')
        showings = Showing.get_by_cinema_date(1, today.isoformat())
    showing = showings[0]
    
    for _ in range(5):
        BookingManager.create_booking(showing.showing_id, 11, 'lower_hall', 1, 'John', 'j@m.com', '123', 10.0, conn)
        
    report = ReportManager.monthly_revenue(1, today.year, today.month, conn)
    assert report["total_bookings"] >= 5
    assert report["total_revenue"] >= 50.0


# 9. Reporting: Staff leaderboard
def test_staff_leaderboard_ordering(setup_integration_db):
    conn = setup_integration_db
    today = datetime.date.today()
    showings = Showing.get_by_cinema_date(1, today.isoformat())
    if not showings:
        conn.execute("INSERT INTO screens (screen_id, cinema_id, screen_number, total_capacity, lower_hall_seats, upper_gallery_seats, vip_seats) VALUES (96, 1, 96, 100, 30, 60, 10)")
        Showing.create(1, 96, 1, today.isoformat(), 'morning')
        showings = Showing.get_by_cinema_date(1, today.isoformat())
    showing = showings[0]
    
    # Staff 11 -> 3 bookings
    for _ in range(3):
        BookingManager.create_booking(showing.showing_id, 11, 'lower_hall', 1, 'A', 'a@m.com', '1', 10.0, conn)
        
    # Staff 12 -> 1 booking
    BookingManager.create_booking(showing.showing_id, 12, 'lower_hall', 1, 'B', 'b@m.com', '2', 10.0, conn)
    
    # Staff 13 -> 5 bookings
    for _ in range(5):
        BookingManager.create_booking(showing.showing_id, 13, 'lower_hall', 1, 'C', 'c@m.com', '3', 10.0, conn)
        
    leaderboard = ReportManager.staff_booking_leaderboard(1, today.year, today.month, conn)
    
    # Staff 13 should be ranked 1st
    assert leaderboard[0]["staff_full_name"] == "staff 3"
    assert leaderboard[0]["total_bookings"] >= 5


# 10. Waitlist: Trigger on cancellation
def test_waitlist_trigger_on_cancellation(setup_integration_db):
    conn = setup_integration_db
    conn.execute("INSERT INTO screens (screen_id, cinema_id, screen_number, total_capacity, lower_hall_seats, upper_gallery_seats, vip_seats) VALUES (99, 1, 99, 2, 2, 0, 0)")
    film = Film.create("Waitlist Film", "Action", "12A", 120)
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    showing = Showing.create(1, 99, film.film_id, tomorrow, 'morning')
    
    # Fill capacity (2 seats)
    booking = BookingManager.create_booking(showing.showing_id, 11, 'lower_hall', 2, 'A', 'a@m.com', '123', 10.0, conn)
    
    # Join Waitlist
    join_waitlist(showing.showing_id, "Wait Customer", "wait@m.com", "999", 2)
    
    # Cancel the booking
    CancellationManager.cancel_booking(booking["booking_ref"], conn)
    
    # Simulate application processing the waitlist upon cancellation
    process_waitlist(showing.showing_id, 2)
    
    wait_entry = conn.execute("SELECT status FROM waitlist WHERE customer_name = 'Wait Customer'").fetchone()
    assert wait_entry["status"] == "offered"
