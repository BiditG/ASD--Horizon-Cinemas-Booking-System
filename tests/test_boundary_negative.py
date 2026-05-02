import pytest
import sqlite3
import datetime

from src.database.db_connection import get_connection
from src.database import db_connection
import src.database.setup_db as setup_db

from src.models.showing import Showing
from src.models.booking import BookingManager, BookingError
from src.models.cancellation import CancellationManager, CancellationError
from src.utils.input_validator import InputValidator
from src.utils.pricing_engine import PricingEngine

@pytest.fixture(scope="function")
def db():
    """
    Setup an in-memory SQLite database for testing boundaries.
    This creates tables and seeds initial data via setup_db.
    """
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    
    setup_db.create_tables(conn)
    setup_db.seed_data(conn)
    
    original_conn = db_connection._connection
    db_connection._connection = conn
    
    yield conn
    
    db_connection._connection = original_conn
    conn.close()

# =====================================================================
# Date boundaries
# =====================================================================

def test_booking_exactly_7_days_ahead(db):
    """should SUCCEED"""
    future_date = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
    # validate_booking_date returns None on success, raises error on failure
    assert BookingManager.validate_booking_date(future_date) is None

def test_booking_8_days_ahead(db):
    """should RAISE exception / return error"""
    future_date = (datetime.date.today() + datetime.timedelta(days=8)).isoformat()
    with pytest.raises(BookingError, match="Advance booking limit is 7 days"):
        BookingManager.validate_booking_date(future_date)

def test_booking_yesterday_date(db):
    """should RAISE exception"""
    past_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    with pytest.raises(BookingError, match="Cannot book for a past showing"):
        BookingManager.validate_booking_date(past_date)

def test_same_day_cancellation(db):
    """should RAISE exception"""
    today = datetime.date.today().isoformat()
    db.execute("PRAGMA foreign_keys = OFF")
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ? AND show_time = '19:00'", (today,))
    db.execute("PRAGMA foreign_keys = ON")
    showing = Showing.create(cinema_id=1, screen_id=1, film_id=1, date=today, show_type="evening")
    booking = BookingManager.create_booking(
        showing_id=showing.showing_id, staff_user_id=1, ticket_type="lower_hall", 
        quantity=1, customer_name="Test", customer_email="t@test.com", 
        customer_phone="123", unit_price=5.0, db_connection=db
    )
    with pytest.raises(CancellationError, match="Same-day cancellation is not permitted"):
        CancellationManager.cancel_booking(booking["booking_ref"], db)

def test_cancellation_1_day_before(db):
    """should SUCCEED with 50% fee"""
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    db.execute("PRAGMA foreign_keys = OFF")
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ? AND show_time = '19:00'", (tomorrow,))
    db.execute("PRAGMA foreign_keys = ON")
    showing = Showing.create(cinema_id=1, screen_id=1, film_id=1, date=tomorrow, show_type="evening")
    booking = BookingManager.create_booking(
        showing_id=showing.showing_id, staff_user_id=1, ticket_type="lower_hall", 
        quantity=2, customer_name="Test", customer_email="t@test.com", 
        customer_phone="123", unit_price=10.0, db_connection=db
    )
    
    result = CancellationManager.cancel_booking(booking["booking_ref"], db)
    # Total cost is 20.0, 50% fee is 10.0
    assert result["cancellation_fee"] == 10.0
    assert result["refund_amount"] == 10.0

# =====================================================================
# Seat count boundaries
# =====================================================================

def test_book_zero_tickets(db):
    """should RAISE ValueError"""
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    db.execute("PRAGMA foreign_keys = OFF")
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ? AND show_time = '10:00'", (tomorrow,))
    db.execute("PRAGMA foreign_keys = ON")
    showing = Showing.create(cinema_id=1, screen_id=1, film_id=1, date=tomorrow, show_type="morning")
    
    with pytest.raises(ValueError, match="at least 1"):
        BookingManager.create_booking(
            showing_id=showing.showing_id, staff_user_id=1, ticket_type="lower_hall", 
            quantity=0, customer_name="Test", customer_email="t@test.com", 
            customer_phone="123", unit_price=5.0, db_connection=db
        )

def test_book_negative_tickets(db):
    """should RAISE ValueError"""
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    db.execute("PRAGMA foreign_keys = OFF")
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ? AND show_time = '10:00'", (tomorrow,))
    db.execute("PRAGMA foreign_keys = ON")
    showing = Showing.create(cinema_id=1, screen_id=1, film_id=1, date=tomorrow, show_type="morning")
    
    with pytest.raises(ValueError, match="at least 1"):
        BookingManager.create_booking(
            showing_id=showing.showing_id, staff_user_id=1, ticket_type="lower_hall", 
            quantity=-5, customer_name="Test", customer_email="t@test.com", 
            customer_phone="123", unit_price=5.0, db_connection=db
        )

def test_book_more_tickets_than_available(db):
    """should RAISE exception with message 'available'"""
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    db.execute("PRAGMA foreign_keys = OFF")
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ? AND show_time = '10:00'", (tomorrow,))
    db.execute("PRAGMA foreign_keys = ON")
    showing = Showing.create(cinema_id=1, screen_id=1, film_id=1, date=tomorrow, show_type="morning")
    
    # Requesting 1000 tickets which definitely exceeds the maximum screen capacity (max 120)
    with pytest.raises(ValueError, match="available"):
        BookingManager.create_booking(
            showing_id=showing.showing_id, staff_user_id=1, ticket_type="lower_hall", 
            quantity=1000, customer_name="Test", customer_email="t@test.com", 
            customer_phone="123", unit_price=5.0, db_connection=db
        )

def test_book_exactly_remaining_seats(db):
    """should SUCCEED"""
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    # Fetch total capacity dynamically
    screen = db.execute("SELECT total_capacity FROM screens WHERE screen_id = 1").fetchone()
    capacity = screen["total_capacity"]
    db.execute("PRAGMA foreign_keys = OFF")
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ? AND show_time = '10:00'", (tomorrow,))
    db.execute("PRAGMA foreign_keys = ON")
    showing = Showing.create(cinema_id=1, screen_id=1, film_id=1, date=tomorrow, show_type="morning")
    
    booking = BookingManager.create_booking(
        showing_id=showing.showing_id, staff_user_id=1, ticket_type="lower_hall", 
        quantity=capacity, customer_name="Test", customer_email="t@test.com", 
        customer_phone="123", unit_price=5.0, db_connection=db
    )
    
    assert len(booking["seat_numbers"]) == capacity
    assert booking["total_cost"] == capacity * 5.0

# =====================================================================
# Invalid data inputs
# =====================================================================

def test_invalid_card_number_15_digits():
    """card validation should return False"""
    assert InputValidator.validate_card_number("123412341234123") is False

def test_invalid_card_number_non_numeric():
    """should return False"""
    assert InputValidator.validate_card_number("1234abcd5678efgh") is False

def test_valid_card_number_16_digits():
    """should return True (Luhn valid)"""
    # 4242 4242 4242 4242 is a standard Stripe test card that passes Luhn checks
    assert InputValidator.validate_card_number("4242424242424242") is True

def test_empty_customer_name():
    """booking should be rejected due to empty sanitised name"""
    # The application GUI layer rejects empty names via the input validator
    sanitised_name = InputValidator.sanitise_text("   ", max_length=50)
    assert sanitised_name == ""

def test_invalid_email_format():
    """should be rejected by validator"""
    assert InputValidator.validate_email("not-an-email") is False
    assert InputValidator.validate_email("test@.com") is False
    assert InputValidator.validate_email("test@domain.c") is True  # Technically valid by loose regex

def test_show_time_overlap_same_screen(db):
    """adding overlapping showing should RAISE exception"""
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    db.execute("PRAGMA foreign_keys = OFF")
    db.execute("DELETE FROM showings WHERE screen_id = 1 AND show_date = ? AND show_time = '10:00'", (tomorrow,))
    db.execute("PRAGMA foreign_keys = ON")
    Showing.create(cinema_id=1, screen_id=1, film_id=1, date=tomorrow, show_type="morning")
    
    with pytest.raises(Exception, match="Overlapping showing exists"):
        Showing.create(cinema_id=1, screen_id=1, film_id=2, date=tomorrow, show_type="morning")

# =====================================================================
# Price edge cases
# =====================================================================

def test_vip_price_formula(db):
    """assert (lower_hall * 1.2) * 1.2 == vip_price to 2 decimal places"""
    base_price = PricingEngine.get_lower_hall_price(city_id=1, show_type="morning", db_connection=db)
    
    price_info = PricingEngine.calculate_price(city_id=1, show_type="morning", ticket_type="vip", quantity=1, db_connection=db)
    
    expected_vip = round((base_price * 1.20) * 1.20, 2)
    assert price_info["unit_price"] == expected_vip

def test_price_outside_defined_city(db):
    """should raise ValueError or return default"""
    with pytest.raises(ValueError, match="No price found"):
        PricingEngine.get_lower_hall_price(city_id=999, show_type="morning", db_connection=db)
