import pytest
import sqlite3
import datetime

from src.database.db_connection import get_connection
from src.database import db_connection
import src.database.setup_db as setup_db
from src.models.cinema import Cinema
from src.models.screen import Screen
from src.models.film import Film
from src.models.showing import Showing
from src.models.booking import BookingManager, BookingError
from src.models.user import User
from src.utils.pricing_engine import PricingEngine

@pytest.fixture(scope="function")
def db():
    """
    Setup an in-memory SQLite database for testing.
    This creates tables and seeds initial data via setup_db.
    It overrides the singleton connection in db_connection.
    """
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    
    setup_db.create_tables(conn)
    setup_db.seed_data(conn)
    
    # Store original connection and swap with in-memory one
    original_conn = db_connection._connection
    db_connection._connection = conn
    
    yield conn
    
    # Restore and close
    db_connection._connection = original_conn
    conn.close()

# ------------------------------------------------------------------------------
# Cinema model tests
# ------------------------------------------------------------------------------

def test_cinema_creation_valid(db):
    """assert all fields stored correctly"""
    cinema = Cinema.create(city_id=1, name="Test Cinema", location="Test Location")
    assert cinema.cinema_id is not None
    assert cinema.cinema_name == "Test Cinema"
    assert cinema.location == "Test Location"
    assert cinema.city_id == 1
    assert cinema.is_active is True

def test_cinema_city_validation(db):
    """assert only valid cities accepted"""
    # Attempt to create a cinema in a non-existent city (e.g., city_id 999)
    # The foreign key constraint should raise a DatabaseError (wrapping IntegrityError)
    with pytest.raises(sqlite3.DatabaseError):
        Cinema.create(city_id=999, name="Test Cinema", location="Test Location")

def test_add_screen_to_cinema(db):
    """assert screen count increases"""
    initial_screens = Screen.get_by_cinema(1)
    
    # Manually insert a screen to the cinema
    db.execute(
        """INSERT INTO screens (cinema_id, screen_number, total_capacity, 
           lower_hall_seats, upper_gallery_seats, vip_seats) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (1, 99, 100, 30, 60, 10)
    )
    db.commit()
    
    new_screens = Screen.get_by_cinema(1)
    assert len(new_screens) == len(initial_screens) + 1

# ------------------------------------------------------------------------------
# Screen model tests
# ------------------------------------------------------------------------------

def test_screen_capacity_range(db):
    """assert capacity between 50–120, reject outside range"""
    screens = db.execute("SELECT * FROM screens").fetchall()
    for s in screens:
        assert 50 <= s["total_capacity"] <= 120

def test_lower_hall_seat_count(db):
    """assert ~30% of capacity assigned to lower hall"""
    screens = db.execute("SELECT * FROM screens").fetchall()
    for s in screens:
        expected_lower = int(s["total_capacity"] * 0.3)
        assert s["lower_hall_seats"] == expected_lower

# ------------------------------------------------------------------------------
# Film model tests
# ------------------------------------------------------------------------------

def test_film_creation(db):
    """assert title, genre, age_rating, duration stored correctly"""
    film = Film.create(title="Test Film", genre="Action", age_rating="15", duration_mins=120)
    assert film.title == "Test Film"
    assert film.genre == "Action"
    assert film.age_rating == "15"
    assert film.duration_mins == 120

def test_film_age_rating_valid_values(db):
    """assert only valid BBFC ratings accepted (U, PG, 12A, 12, 15, 18)"""
    with pytest.raises(ValueError, match="Invalid age rating"):
        Film.create(title="Test Film", genre="Action", age_rating="INVALID", duration_mins=120)

# ------------------------------------------------------------------------------
# Showing model tests
# ------------------------------------------------------------------------------

def test_showing_creation(db):
    """assert film, screen, show_time, date stored"""
    date_str = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ?", (date_str,))
    showing = Showing.create(cinema_id=1, screen_id=1, film_id=1, date=date_str, show_type="morning")
    
    assert showing.film_id == 1
    assert showing.screen_id == 1
    assert showing.show_date == date_str
    assert showing.show_time == "10:00"

def test_no_overlapping_shows_same_screen(db):
    """assert two showings on same screen at same time raises an error"""
    date_str = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ?", (date_str,))
    Showing.create(cinema_id=1, screen_id=1, film_id=1, date=date_str, show_type="morning")
    
    with pytest.raises(Exception, match="Overlapping showing exists"):
        Showing.create(cinema_id=1, screen_id=1, film_id=2, date=date_str, show_type="morning")

def test_advance_booking_limit(db):
    """assert bookings beyond 7 days ahead are rejected"""
    future_date = (datetime.date.today() + datetime.timedelta(days=8)).isoformat()
    
    with pytest.raises(BookingError, match="Advance booking limit is 7 days"):
        BookingManager.validate_booking_date(future_date)

# ------------------------------------------------------------------------------
# Booking model tests
# ------------------------------------------------------------------------------

def test_unique_booking_reference(db):
    """assert two bookings get different references"""
    date_str = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ?", (date_str,))
    showing = Showing.create(cinema_id=1, screen_id=1, film_id=1, date=date_str, show_type="morning")
    
    # Using admin user (user_id=1) to bypass home cinema restrictions
    booking1 = BookingManager.create_booking(
        showing_id=showing.showing_id, staff_user_id=1, ticket_type="lower_hall", 
        quantity=1, customer_name="John Doe", customer_email="john@example.com", 
        customer_phone="123", unit_price=5.0, db_connection=db
    )
    booking2 = BookingManager.create_booking(
        showing_id=showing.showing_id, staff_user_id=1, ticket_type="lower_hall", 
        quantity=1, customer_name="Jane Doe", customer_email="jane@example.com", 
        customer_phone="123", unit_price=5.0, db_connection=db
    )
    
    assert booking1["booking_ref"] != booking2["booking_ref"]

def test_booking_total_cost_lower_hall(db):
    """assert correct price calculated"""
    date_str = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ?", (date_str,))
    showing = Showing.create(cinema_id=1, screen_id=1, film_id=1, date=date_str, show_type="morning")
    
    # Base lower_hall price in morning is 5.0
    unit_price = 5.0
    booking = BookingManager.create_booking(
        showing_id=showing.showing_id, staff_user_id=1, ticket_type="lower_hall", 
        quantity=2, customer_name="Test User", customer_email="t@test.com", 
        customer_phone="123", unit_price=unit_price, db_connection=db
    )
    
    assert booking["total_cost"] == 10.0

def test_booking_total_cost_vip(db):
    """assert VIP price = lower_hall * 1.20 * 1.20"""
    date_str = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    
    # Create a screen for London (city_id=4)
    db.execute("INSERT INTO cinemas (cinema_id, city_id, cinema_name) VALUES (99, 4, 'London Cinema')")
    db.execute("INSERT INTO screens (cinema_id, screen_number, total_capacity, lower_hall_seats, upper_gallery_seats, vip_seats) VALUES (99, 1, 100, 30, 60, 10)")
    screen_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    db.execute("DELETE FROM showings WHERE screen_id = ? AND show_date = ?", (screen_id, date_str))
    showing = Showing.create(cinema_id=99, screen_id=screen_id, film_id=1, date=date_str, show_type="evening")
    
    # London evening base price is 12.0
    # VIP = 12.0 * 1.20 * 1.20 = 17.28
    price_info = PricingEngine.calculate_price(4, "evening", "vip", 2, db)
    assert price_info["unit_price"] == 17.28
    
    booking = BookingManager.create_booking(
        showing_id=showing.showing_id, staff_user_id=1, ticket_type="vip", 
        quantity=2, customer_name="VIP", customer_email="vip@vip.com", 
        customer_phone="123", unit_price=price_info["unit_price"], db_connection=db
    )
    
    assert booking["total_cost"] == 34.56

def test_booking_receipt_fields(db):
    """assert receipt contains all required fields"""
    date_str = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ?", (date_str,))
    showing = Showing.create(cinema_id=1, screen_id=1, film_id=1, date=date_str, show_type="morning")
    
    booking = BookingManager.create_booking(
        showing_id=showing.showing_id, staff_user_id=1, ticket_type="lower_hall", 
        quantity=1, customer_name="Receipt User", customer_email="r@test.com", 
        customer_phone="123", unit_price=5.0, db_connection=db
    )
    
    assert "booking_ref" in booking
    assert "customer_name" in booking
    assert "total_cost" in booking
    assert "seat_numbers" in booking

# ------------------------------------------------------------------------------
# User model tests
# ------------------------------------------------------------------------------

def test_user_role_validation():
    """assert only 'manager', 'admin', 'staff' ('booking_staff') accepted"""
    User(1, 1, "mngr", "hash", "manager", "m@c.com", "manager")
    User(2, 1, "admn", "hash", "admin", "a@c.com", "admin")
    User(3, 1, "stff", "hash", "staff", "s@c.com", "staff")
    
    with pytest.raises(ValueError, match="Invalid role"):
        User(4, 1, "invalid", "hash", "name", "e@c.com", "booking_staff")

def test_password_hashing():
    """assert stored password != plain text"""
    plain = "secure_password"
    hashed = User.hash_password(plain)
    
    assert hashed != plain
    assert User.verify_password(plain, hashed) is True

def test_user_registration_create_user(db):
    """assert User.create_user successfully inserts into DB"""
    User.create_user("newstaff", "password123", "New Staff Member", "new@staff.com", "staff", cinema_id=1)
    
    conn = get_connection()
    user_row = conn.execute("SELECT * FROM users WHERE username = ?", ("newstaff",)).fetchone()
    
    assert user_row is not None
    assert user_row["full_name"] == "New Staff Member"
    assert user_row["role"] == "staff"
    assert User.verify_password("password123", user_row["password_hash"])

def test_create_user_duplicate_username(db):
    """assert create_user raises ValueError for existing username"""
    User.create_user("duplicate", "pass1", "Name 1", "e1@test.com", "staff")
    
    with pytest.raises(ValueError, match="already exists"):
        User.create_user("duplicate", "pass2", "Name 2", "e2@test.com", "admin")

def test_get_users_by_role(db):
    """assert get_users_by_role returns correct subset"""
    User.create_user("admin_test", "pass", "Admin Test", "a@t.com", "admin")
    User.create_user("staff_test", "pass", "Staff Test", "s@t.com", "staff")
    
    admins = User.get_users_by_role("admin")
    staff_members = User.get_users_by_role("staff")
    
    assert any(u["username"] == "admin_test" for u in admins)
    assert not any(u["username"] == "staff_test" for u in admins)
    assert any(u["username"] == "staff_test" for u in staff_members)

def test_delete_user(db):
    """assert user can be permanently removed"""
    # Create a dummy user
    User.create_user(username="temp_user", password="password123", full_name="Temp", email="t@t.com", role="staff")
    user = db.execute("SELECT user_id FROM users WHERE username = 'temp_user'").fetchone()
    uid = user["user_id"]
    
    # Delete
    success = User.delete_user(uid)
    assert success is True
    
    # Verify gone
    user_gone = db.execute("SELECT * FROM users WHERE user_id = ?", (uid,)).fetchone()
    assert user_gone is None

# ------------------------------------------------------------------------------
# Pricing engine tests
# ------------------------------------------------------------------------------

def test_price_birmingham_morning(db):
    """assert £5 for Birmingham morning lower hall"""
    price = PricingEngine.get_lower_hall_price(1, "morning", db)
    assert price == 5.0

def test_price_london_evening_vip(db):
    """assert correct VIP calculation for London evening (£12 * 1.2 * 1.2 = £17.28)"""
    price_info = PricingEngine.calculate_price(4, "evening", "vip", 1, db)
    assert price_info["total_price"] == 17.28

def test_upper_gallery_20_percent_higher(db):
    """assert upper gallery = lower hall * 1.20"""
    base_price = PricingEngine.get_lower_hall_price(1, "morning", db)
    price_info = PricingEngine.calculate_price(1, "morning", "upper_gallery", 1, db)
    
    assert price_info["unit_price"] == round(base_price * 1.20, 2)

def test_pricing_breakdown(db):
    """Additional pricing engine test to ensure breakdown is generated"""
    price_info = PricingEngine.calculate_price(1, "morning", "vip", 2, db)
    assert "Vip @ £7.20 = £14.40" in price_info["price_breakdown"]
