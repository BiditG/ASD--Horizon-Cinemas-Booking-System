"""
src/utils/bulk_seat_selector.py
================================
Greedy bulk seat selection algorithm for group bookings (>=10 seats).

Strategy:
1. Gather all available seats for the showing in the requested ticket_type zone.
2. Group them by their row letter (A, B, V…).
3. For each row, detect contiguous runs of available seats.
4. Greedily fill the largest runs first to minimise the number of rows used.
5. If no single row can hold the whole group, split into the FEWEST rows possible
   (e.g. 12 seats → one row of 8 + one row of 4, not six rows of 2).

Returns a list of seat-number strings (e.g. ["A1","A2",…,"A12"]).
Returns None and a max_available int if there are simply not enough seats at all.
"""

from __future__ import annotations
from collections import defaultdict
import re
from src.database.db_connection import get_connection


def _parse_seat(seat_num: str) -> tuple[str, int]:
    """Split "A12" → ("A", 12), "V3" → ("V", 3)."""
    m = re.match(r"([A-Za-z]+)(\d+)", seat_num)
    if not m:
        return ("", 0)
    return m.group(1), int(m.group(2))


def _contiguous_runs(seat_numbers: list[int]) -> list[list[int]]:
    """Given a sorted list of ints, return lists of contiguous runs."""
    if not seat_numbers:
        return []
    runs: list[list[int]] = []
    current = [seat_numbers[0]]
    for n in seat_numbers[1:]:
        if n == current[-1] + 1:
            current.append(n)
        else:
            runs.append(current)
            current = [n]
    runs.append(current)
    return runs


def bulk_select_seats(
    showing_id: int,
    ticket_type: str,
    quantity: int,
) -> tuple[list[str] | None, int]:
    """
    Select `quantity` seats for the given showing and ticket_type zone.

    Returns:
        (selected_seat_numbers, max_available)
        where selected_seat_numbers is None if insufficient seats exist.
    """
    conn = get_connection()

    # Determine zone prefix
    prefix_map = {
        "lower_hall":    "A",
        "upper_gallery": "B",
        "vip":           "V",
    }
    prefix = prefix_map.get(ticket_type, "A")

    # Fetch all seats in this zone
    cursor = conn.execute("""
        SELECT sc.lower_hall_seats, sc.upper_gallery_seats, sc.vip_seats
        FROM showings sh
        JOIN screens sc ON sh.screen_id = sc.screen_id
        WHERE sh.showing_id = ?
    """, (showing_id,))
    row = cursor.fetchone()
    if not row:
        return None, 0

    capacity_map = {
        "lower_hall":    ("lower_hall_seats",    "A"),
        "upper_gallery": ("upper_gallery_seats",  "B"),
        "vip":           ("vip_seats",            "V"),
    }
    col, _ = capacity_map[ticket_type]
    total_in_zone = row[col]

    # All seat numbers in zone
    all_zone = [f"{prefix}{i}" for i in range(1, total_in_zone + 1)]

    # Already booked seats
    cursor = conn.execute("""
        SELECT t.seat_number
        FROM tickets t
        JOIN bookings b ON t.booking_id = b.booking_id
        WHERE b.showing_id = ? AND b.booking_status = 'Active'
    """, (showing_id,))
    booked = set(r["seat_number"] for r in cursor.fetchall())

    available = [s for s in all_zone if s not in booked]
    max_available = len(available)

    if max_available < quantity:
        return None, max_available

    # Group by row letter (A, B, V) and then number within row
    # Seat map uses 10 seats per row, so row letter = prefix, row_number = ceil(i/10)
    ROW_SIZE = 10
    row_groups: dict[int, list[int]] = defaultdict(list)
    for s in available:
        _, num = _parse_seat(s)
        row_idx = (num - 1) // ROW_SIZE
        row_groups[row_idx].append(num)

    # Build runs within each row, sorted by run length descending
    all_runs: list[list[str]] = []
    for row_idx in sorted(row_groups.keys()):
        nums = sorted(row_groups[row_idx])
        for run in _contiguous_runs(nums):
            all_runs.append([f"{prefix}{n}" for n in run])

    # Sort runs largest first
    all_runs.sort(key=lambda r: -len(r))

    # Greedily fill from largest run
    selected: list[str] = []
    remaining = quantity

    for run in all_runs:
        if remaining <= 0:
            break
        take = min(len(run), remaining)
        selected.extend(run[:take])
        remaining -= take

    if remaining > 0:
        # Shouldn't happen since we checked max_available, but be safe
        return None, max_available

    return selected, max_available
