"""
tests/test_seat_recommender.py
"""

import pytest
from unittest.mock import MagicMock, patch
from src.utils.seat_recommender import recommend_seats

@pytest.fixture
def mock_db():
    with patch("src.utils.seat_recommender.get_connection") as mock_get_conn:
        conn = MagicMock()
        mock_get_conn.return_value = conn
        yield conn

def test_recommend_single_seat_finds_center(mock_db):
    """Test that a single seat recommendation prefers the center of the row."""
    mock_db.execute.side_effect = [
        MagicMock(fetchone=lambda: {"lower_hall_seats": 20, "upper_gallery_seats": 20, "vip_seats": 10}),
        MagicMock(fetchall=lambda: []) # No booked seats
    ]
    
    rec = recommend_seats(1, "lower_hall", 1)
    
    assert len(rec) == 1
    # Center of 10-seat row (0-9) is 4 or 5.
    # So A5 or A6.
    assert rec[0] in ["A5", "A6"]

def test_recommend_group_of_4_keeps_together(mock_db):
    """Test that a group of 4 is placed contiguously in the same row."""
    # A5 is booked, so center of first row is disrupted. 
    # Algorithm should find a contiguous block of 4 elsewhere, perhaps row 1 (A11-A20) or left/right side of row 0.
    mock_db.execute.side_effect = [
        MagicMock(fetchone=lambda: {"lower_hall_seats": 30, "upper_gallery_seats": 20, "vip_seats": 10}),
        MagicMock(fetchall=lambda: [{"seat_number": "A5"}])
    ]
    
    rec = recommend_seats(1, "lower_hall", 4)
    
    assert len(rec) == 4
    # Extract numerical part to verify they are contiguous
    nums = sorted([int(s[1:]) for s in rec])
    assert nums[3] - nums[0] == 3 # difference between max and min is 3 => 4 contiguous seats

def test_recommend_nearly_full_screen(mock_db):
    """Test fallback when no contiguous seats are available (nearly full screen)."""
    # Book all VIP seats except V2 and V9
    booked = [{"seat_number": f"V{i}"} for i in range(1, 11) if i not in (2, 9)]
    
    mock_db.execute.side_effect = [
        MagicMock(fetchone=lambda: {"lower_hall_seats": 10, "upper_gallery_seats": 10, "vip_seats": 10}),
        MagicMock(fetchall=lambda: booked)
    ]
    
    rec = recommend_seats(1, "vip", 2)
    
    assert len(rec) == 2
    # The only 2 seats left are V2 and V9
    assert "V2" in rec
    assert "V9" in rec
