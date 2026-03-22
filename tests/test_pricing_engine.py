"""
tests/test_pricing_engine.py
============================
Pytest suite for the HCBS Pricing Engine.
"""

import sqlite3
import pytest
import datetime
from src.utils.pricing_engine import PricingEngine

@pytest.fixture
def memory_db():
    """Create an in-memory SQLite database populated with HCBS price tiers."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE prices (
            price_id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id INTEGER,
            show_type TEXT NOT NULL,
            lower_hall_price REAL NOT NULL,
            effective_from TEXT NOT NULL
        )
        """
    )
    
    # Birmingham (1)
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (1, 'morning', 5.00, '2025-01-01')")
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (1, 'afternoon', 6.00, '2025-01-01')")
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (1, 'evening', 7.00, '2025-01-01')")
    
    # Bristol (2)
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (2, 'morning', 6.00, '2025-01-01')")
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (2, 'afternoon', 7.00, '2025-01-01')")
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (2, 'evening', 8.00, '2025-01-01')")

    # Cardiff (3)
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (3, 'morning', 5.00, '2025-01-01')")
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (3, 'afternoon', 6.00, '2025-01-01')")
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (3, 'evening', 7.00, '2025-01-01')")

    # London (4)
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (4, 'morning', 10.00, '2025-01-01')")
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (4, 'afternoon', 11.00, '2025-01-01')")
    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (4, 'evening', 12.00, '2025-01-01')")
    
    yield conn
    conn.close()

# ── 1. Base Price tests ───────────────────────────────────────────────────────

@pytest.mark.parametrize("city_id, show_type, expected_price", [
    (1, "morning", 5.00),    # Birmingham
    (1, "afternoon", 6.00),
    (1, "evening", 7.00),
    (2, "morning", 6.00),    # Bristol
    (2, "afternoon", 7.00),
    (2, "evening", 8.00),
    (4, "morning", 10.00),   # London
    (4, "afternoon", 11.00),
    (4, "evening", 12.00)
])
def test_get_lower_hall_price(memory_db, city_id, show_type, expected_price):
    price = PricingEngine.get_lower_hall_price(city_id, show_type, memory_db)
    assert price == expected_price

def test_get_lower_hall_price_invalid_city(memory_db):
    with pytest.raises(ValueError):
        PricingEngine.get_lower_hall_price(99, "morning", memory_db)

# ── 2. Calculation logic tests ────────────────────────────────────────────────

def test_calculate_price_lower_hall(memory_db):
    # Birmingham evening base = 7.00
    res = PricingEngine.calculate_price(1, "evening", "lower_hall", 3, memory_db)
    assert res["unit_price"] == 7.00
    assert res["total_price"] == 21.00
    assert res["quantity"] == 3
    assert res["ticket_type"] == "lower_hall"

def test_calculate_price_upper_gallery_uplift(memory_db):
    # London evening base = 12.00. Upper gallery = 12.00 * 1.20 = 14.40
    res = PricingEngine.calculate_price(4, "evening", "upper_gallery", 2, memory_db)
    assert res["unit_price"] == 14.40
    assert res["total_price"] == 28.80

def test_calculate_price_vip_uplift(memory_db):
    # Birmingham morning base = 5.00. 
    # Upper gallery = 5 * 1.2 = 6.00
    # VIP = 6 * 1.2 = 7.20
    res = PricingEngine.calculate_price(1, "morning", "vip", 1, memory_db)
    assert res["unit_price"] == 7.20
    assert res["total_price"] == 7.20

def test_price_breakdown(memory_db):
    # Bristol afternoon base = 7.00
    bd = PricingEngine.get_price_breakdown(2, "afternoon", memory_db)
    assert bd["lower_hall"] == 7.00
    assert bd["upper_gallery"] == 8.40   # 7 * 1.2
    assert bd["vip"] == 10.08            # 8.4 * 1.2

# ── 3. Time validation tests ──────────────────────────────────────────────────

@pytest.mark.parametrize("time_val, expected", [
    ("08:00", "morning"),
    ("11:59", "morning"),
    ("12:00", "afternoon"),
    ("16:59", "afternoon"),
    ("17:00", "evening"),
    ("23:59", "evening"),
    (datetime.time(10, 30), "morning"),
    (datetime.time(15, 45), "afternoon"),
    (datetime.time(20, 15), "evening"),
])
def test_validate_show_type(time_val, expected):
    assert PricingEngine.validate_show_type(time_val) == expected

def test_validate_show_type_invalid_string():
    with pytest.raises(ValueError):
        PricingEngine.validate_show_type("25:99")
