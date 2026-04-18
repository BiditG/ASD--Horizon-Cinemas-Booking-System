"""
tests/test_bulk_seat_selector.py
"""

import pytest
from unittest.mock import MagicMock, patch


def _make_db(total_zone_seats: int, booked_nums: list[int], ticket_type: str = "lower_hall"):
    """
    Build a mock DB connection fixture.
    total_zone_seats: how many seats exist in the zone
    booked_nums:      seat numbers already booked (e.g. [1, 2, 3])
    """
    conn = MagicMock()

    capacity_row = MagicMock()
    capacity_row.__getitem__ = lambda self, key: {
        "lower_hall_seats":    total_zone_seats if ticket_type == "lower_hall"    else 0,
        "upper_gallery_seats": total_zone_seats if ticket_type == "upper_gallery" else 0,
        "vip_seats":           total_zone_seats if ticket_type == "vip"           else 0,
    }[key]

    prefix = {"lower_hall": "A", "upper_gallery": "B", "vip": "V"}[ticket_type]

    def _make_seat_row(n):
        r = MagicMock()
        r.__getitem__ = lambda self, key: f"{prefix}{n}" if key == "seat_number" else None
        return r

    booked_rows = [_make_seat_row(n) for n in booked_nums]

    cur1 = MagicMock(); cur1.fetchone.return_value = capacity_row
    cur2 = MagicMock(); cur2.fetchall.return_value = booked_rows
    conn.execute.side_effect = [cur1, cur2]
    return conn


class TestBulkSelectSeats:
    def test_selects_contiguous_block_first(self):
        """With 30 available lower-hall seats, selecting 10 should return A1-A10 (first full row)."""
        with patch("src.utils.bulk_seat_selector.get_connection") as mock_conn:
            mock_conn.return_value = _make_db(total_zone_seats=30, booked_nums=[])
            from src.utils.bulk_seat_selector import bulk_select_seats
            selected, max_avail = bulk_select_seats(showing_id=1, ticket_type="lower_hall", quantity=10)

        assert selected is not None
        assert len(selected) == 10
        assert max_avail == 30
        # Should all be A-prefixed
        assert all(s.startswith("A") for s in selected)
        # Should be numerically contiguous
        nums = sorted(int(s[1:]) for s in selected)
        assert nums == list(range(nums[0], nums[0] + 10))

    def test_splits_across_rows_when_needed(self):
        """
        12 seats requested, but A1-A8 are booked, leaving seats A9-A30.
        The algorithm should still return exactly 12 seats from the available pool.
        """
        with patch("src.utils.bulk_seat_selector.get_connection") as mock_conn:
            mock_conn.return_value = _make_db(total_zone_seats=30, booked_nums=list(range(1, 9)))
            from src.utils.bulk_seat_selector import bulk_select_seats
            selected, max_avail = bulk_select_seats(showing_id=1, ticket_type="lower_hall", quantity=12)

        assert selected is not None
        assert len(selected) == 12
        # All selected seats must be free (not in booked range 1-8)
        nums = [int(s[1:]) for s in selected]
        assert all(n >= 9 for n in nums), f"Got seats with nums: {nums}"

    def test_returns_none_when_insufficient_seats(self):
        """Requesting more seats than available returns (None, max_available)."""
        with patch("src.utils.bulk_seat_selector.get_connection") as mock_conn:
            mock_conn.return_value = _make_db(total_zone_seats=8, booked_nums=[])
            from src.utils.bulk_seat_selector import bulk_select_seats
            selected, max_avail = bulk_select_seats(showing_id=1, ticket_type="lower_hall", quantity=10)

        assert selected is None
        assert max_avail == 8

    def test_vip_zone_prefix(self):
        """VIP seats use 'V' prefix and are correctly selected."""
        with patch("src.utils.bulk_seat_selector.get_connection") as mock_conn:
            mock_conn.return_value = _make_db(total_zone_seats=15, booked_nums=[], ticket_type="vip")
            from src.utils.bulk_seat_selector import bulk_select_seats
            selected, max_avail = bulk_select_seats(showing_id=2, ticket_type="vip", quantity=10)

        assert selected is not None
        assert len(selected) == 10
        assert all(s.startswith("V") for s in selected)

    def test_all_seats_booked_returns_none(self):
        """When the zone is completely full, returns (None, 0)."""
        with patch("src.utils.bulk_seat_selector.get_connection") as mock_conn:
            mock_conn.return_value = _make_db(total_zone_seats=10, booked_nums=list(range(1, 11)))
            from src.utils.bulk_seat_selector import bulk_select_seats
            selected, max_avail = bulk_select_seats(showing_id=3, ticket_type="lower_hall", quantity=10)

        assert selected is None
        assert max_avail == 0
