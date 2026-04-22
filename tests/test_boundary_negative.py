import pytest
import sqlite3
import datetime
import sys
from unittest.mock import MagicMock

# Mock bcrypt just in case it's not present in the test environment (like test_models.py)
mock_bcrypt = MagicMock()
mock_bcrypt.gensalt.return_value = b'salt'
mock_bcrypt.hashpw.return_value = b'hashed_password'
mock_bcrypt.checkpw.return_value = True
sys.modules['bcrypt'] = mock_bcrypt

from src.database import db_connection
from src.database.setup_db import create_tables
from src.models.showing import Showing, ShowingFullError
from src.models.booking import BookingManager, BookingError
from src.models.cancellation import CancellationManager, CancellationError
from src.models.cinema import Cinema
from src.models.film import Film
from src.utils.input_validator import InputValidator
from src.utils.pricing_engine import PricingEngine

@pytest.fixture(autouse=True)
def setup_in_memory_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    create_tables(cursor)
    
    # Patch schema to match model expectations
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

    # Seed lookups needed
    conn.execute("INSERT INTO cities (city_id, city_name) VALUES (1, 'Birmingham')")
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (1, 'morning', 5.0, '2025-01-01')")
    
    conn.execute("INSERT INTO cinemas (cinema_id, city_id, cinema_name) VALUES (1, 1, 'Boundary Cinema')")
    # Insert a dummy staff user
    conn.execute("INSERT INTO users (user_id, cinema_id, username, password_hash, full_name, email, role, is_active) VALUES (1, 1, 'staff', 'hash', 'Test Staff', 'e@m.com', 'staff', 1)")
    
    conn.commit()
    db_connection._connection = conn
    yield conn
    db_connection._connection = None
    conn.close()

def setup_showing(conn, capacity=10, date_offset=1, time='morning'):
    conn.execute("INSERT INTO screens (screen_id, cinema_id, screen_number, total_capacity, lower_hall_seats, upper_gallery_seats, vip_seats) VALUES (1, 1, 1, ?, ?, ?, ?)", (capacity, capacity//3, capacity//3, capacity//3))
    film = Film.create(title="Test", genre="Action", age_rating="12A", duration_mins=100)
    target_date = (datetime.date.today() + datetime.timedelta(days=date_offset)).isoformat()
    return Showing.create(1, 1, film.film_id, target_date, time)


# =====================================================================
# Date Boundaries
# =====================================================================

def test_booking_exactly_7_days_ahead():
    """should SUCCEED"""
    future_date = datetime.date.today() + datetime.timedelta(days=7)
    # Should return None and not raise an exception
    assert BookingManager.validate_booking_date(future_date) is None

def test_booking_8_days_ahead():
    """should RAISE exception / return error"""
    future_date = datetime.date.today() + datetime.timedelta(days=8)
    with pytest.raises(BookingError, match="Advance booking limit is 7 days"):
        BookingManager.validate_booking_date(future_date)

def test_booking_yesterday_date():
    """should RAISE exception"""
    past_date = datetime.date.today() - datetime.timedelta(days=1)
    with pytest.raises(BookingError, match="Cannot book for a past showing"):
        BookingManager.validate_booking_date(past_date)

def test_same_day_cancellation(setup_in_memory_db):
    """should RAISE exception"""
    conn = setup_in_memory_db
    showing = setup_showing(conn, date_offset=0)
    
    booking_dict = BookingManager.create_booking(
        showing.showing_id, 1, 'lower_hall', 1, 'John', 'j@m.com', '123', 5.0, conn
    )
    with pytest.raises(CancellationError, match="Same-day cancellation is not permitted"):
        CancellationManager.cancel_booking(booking_dict['booking_ref'], conn)

def test_cancellation_1_day_before(setup_in_memory_db):
    """should SUCCEED with 50% fee"""
    conn = setup_in_memory_db
    showing = setup_showing(conn, date_offset=1)
    
    booking_dict = BookingManager.create_booking(
        showing.showing_id, 1, 'lower_hall', 1, 'John', 'j@m.com', '123', 5.0, conn
    )
    result = CancellationManager.cancel_booking(booking_dict['booking_ref'], conn)
    assert result['cancellation_fee'] == 2.50 # 50% of 5.0


# =====================================================================
# Seat Count Boundaries
# =====================================================================

def test_book_zero_tickets(setup_in_memory_db):
    """should RAISE ValueError"""
    conn = setup_in_memory_db
    showing = setup_showing(conn)
    with pytest.raises(ValueError):
        # We expect a ValueError either from the UI logic or the backend model validating qty > 0
        BookingManager.create_booking(showing.showing_id, 1, 'lower_hall', 0, 'John', 'j@m.com', '123', 5.0, conn)

def test_book_negative_tickets(setup_in_memory_db):
    """should RAISE ValueError"""
    conn = setup_in_memory_db
    showing = setup_showing(conn)
    with pytest.raises(ValueError):
        BookingManager.create_booking(showing.showing_id, 1, 'lower_hall', -1, 'John', 'j@m.com', '123', 5.0, conn)

def test_book_more_tickets_than_available(setup_in_memory_db):
    """should RAISE exception with message 'Not enough seats' or equivalent"""
    conn = setup_in_memory_db
    showing = setup_showing(conn, capacity=10)
    # The exact message defined in the model is "does not have X seats available."
    with pytest.raises(ValueError, match="does not have 11 seats available."):
        BookingManager.create_booking(showing.showing_id, 1, 'lower_hall', 11, 'John', 'j@m.com', '123', 5.0, conn)

def test_book_exactly_remaining_seats(setup_in_memory_db):
    """should SUCCEED"""
    conn = setup_in_memory_db
    showing = setup_showing(conn, capacity=5)
    booking = BookingManager.create_booking(showing.showing_id, 1, 'lower_hall', 5, 'John', 'j@m.com', '123', 5.0, conn)
    
    # Assert successful booking creation
    assert "booking_ref" in booking
    
    # Ensure remaining seats is now 0
    updated_showing = Showing.get_by_id(showing.showing_id)
    assert updated_showing.seats_remaining == 0


# =====================================================================
# Invalid Data Inputs
# =====================================================================

def test_invalid_card_number_15_digits():
    """card validation should return False"""
    card_15 = "123456789012345"
    assert InputValidator.validate_card_number(card_15) is False

def test_invalid_card_number_non_numeric():
    """should return False"""
    card_alpha = "1234ABCD5678WXYZ"
    assert InputValidator.validate_card_number(card_alpha) is False

def test_valid_card_number_16_digits():
    """should return True (Luhn valid)"""
    # A valid test card number that passes Luhn check
    valid_card = "4242424242424242"
    assert InputValidator.validate_card_number(valid_card) is True

def test_empty_customer_name(setup_in_memory_db):
    """booking should be rejected"""
    # SQLite has a NOT NULL constraint on customer_name
    conn = setup_in_memory_db
    showing = setup_showing(conn)
    with pytest.raises(Exception):
        BookingManager.create_booking(showing.showing_id, 1, 'lower_hall', 1, None, 'j@m.com', '123', 5.0, conn)

def test_invalid_email_format():
    """should be rejected by validator"""
    assert InputValidator.validate_email("john-at-example.com") is False
    assert InputValidator.validate_email("plainaddress") is False

def test_show_time_overlap_same_screen(setup_in_memory_db):
    """adding overlapping showing should RAISE exception"""
    conn = setup_in_memory_db
    showing1 = setup_showing(conn, time='morning')
    
    # Expectation: application rejects overlapping times. If not implemented, test fails (TDD)
    with pytest.raises(Exception):
        # We try to create another morning showing on the same date/screen
        Showing.create(1, 1, showing1.film_id, showing1.show_date, 'morning')


# =====================================================================
# Price Edge Cases
# =====================================================================

def test_vip_price_formula(setup_in_memory_db):
    """assert (lower_hall * 1.2) * 1.2 == vip_price to 2 decimal places"""
    conn = setup_in_memory_db
    # City 1 morning is set to 5.0 in the fixture
    result = PricingEngine.calculate_price(city_id=1, show_type='morning', ticket_type='vip', quantity=1, db_connection=conn)
    # Expected: 5.0 * 1.2 = 6.0; 6.0 * 1.2 = 7.20
    assert result["unit_price"] == 7.20

def test_price_outside_defined_city(setup_in_memory_db):
    """should raise ValueError or return default"""
    conn = setup_in_memory_db
    # City 99 doesn't have prices mapped
    with pytest.raises(ValueError, match="No price found"):
        PricingEngine.calculate_price(city_id=99, show_type='morning', ticket_type='lower_hall', quantity=1, db_connection=conn)
