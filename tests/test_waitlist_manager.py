"""
tests/test_waitlist_manager.py
"""

import pytest
import datetime
from unittest.mock import MagicMock, patch, call

@pytest.fixture
def mock_db():
    with patch("src.utils.waitlist_manager.get_connection") as mock_get_conn:
        conn = MagicMock()
        mock_get_conn.return_value = conn
        yield conn


class TestProcessWaitlist:
    def test_process_waitlist_offers_first_eligible_entry(self, mock_db):
        """
        process_waitlist should update the first 'waiting' entry whose
        num_tickets <= freed_seats to 'offered'.
        """
        now = datetime.datetime.now()

        # Simulate expire-old-offers returning nothing, then 2 waiting entries
        mock_cursor_waiting = MagicMock()
        mock_cursor_waiting.fetchall.return_value = [
            {"waitlist_id": 1, "customer_name": "Alice", "num_tickets": 2},
            {"waitlist_id": 2, "customer_name": "Bob",   "num_tickets": 4},
        ]

        mock_cursor_film = MagicMock()
        mock_cursor_film.fetchone.return_value = {
            "title": "Avengers",
            "show_time": "19:00"
        }

        # execute() calls in order:
        #  1. UPDATE ... expire old offers
        #  2. SELECT ... waiting entries
        #  3. SELECT ... film info
        #  4. UPDATE ... set status='offered' for waitlist_id=1
        mock_db.execute.side_effect = [
            MagicMock(),            # 1. expire UPDATE
            mock_cursor_waiting,    # 2. waiting SELECT
            mock_cursor_film,       # 3. film SELECT
            MagicMock(),            # 4. offer UPDATE for Alice
        ]

        from src.utils.waitlist_manager import process_waitlist
        process_waitlist(showing_id=10, freed_seats=2)

        # Verify the offer UPDATE was issued for waitlist_id=1 (Alice, 2 tickets)
        offer_call_args = mock_db.execute.call_args_list[3]
        sql = offer_call_args[0][0]
        params = offer_call_args[0][1]
        assert "status = 'offered'" in sql
        assert params[1] == 1   # waitlist_id for Alice

    def test_process_waitlist_skips_entry_too_large(self, mock_db):
        """
        Entries whose num_tickets > freed_seats should NOT be offered.
        """
        mock_cursor_waiting = MagicMock()
        mock_cursor_waiting.fetchall.return_value = [
            {"waitlist_id": 5, "customer_name": "Charlie", "num_tickets": 6},
        ]

        mock_cursor_film = MagicMock()
        mock_cursor_film.fetchone.return_value = {
            "title": "Dune",
            "show_time": "14:00"
        }

        mock_db.execute.side_effect = [
            MagicMock(),            # expire UPDATE
            mock_cursor_waiting,    # waiting SELECT
            mock_cursor_film,       # film SELECT
            # No 4th call expected — Charlie is skipped
        ]

        from src.utils.waitlist_manager import process_waitlist
        process_waitlist(showing_id=20, freed_seats=2)

        # Only 3 execute calls should have been made (no offer UPDATE)
        assert mock_db.execute.call_count == 3


class TestExpiredOffers:
    def test_expiry_sql_filters_by_30_minutes(self, mock_db):
        """
        The expire query must reference a 30-minute threshold so that
        offers older than 30 mins are marked 'expired'.
        """
        mock_cursor_waiting = MagicMock()
        mock_cursor_waiting.fetchall.return_value = []  # no waiting entries

        mock_cursor_film = MagicMock()
        mock_cursor_film.fetchone.return_value = {"title": "Test", "show_time": "12:00"}

        mock_db.execute.side_effect = [
            MagicMock(),
            mock_cursor_waiting,
            mock_cursor_film,
        ]

        from src.utils.waitlist_manager import process_waitlist
        process_waitlist(showing_id=99, freed_seats=5)

        # First execute call is the expiry UPDATE — verify it checks 30 minutes
        expire_call = mock_db.execute.call_args_list[0]
        sql = expire_call[0][0]
        assert "30" in sql
        assert "expired" in sql.lower()
        assert "offered_at" in sql
