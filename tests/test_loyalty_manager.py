"""
tests/test_loyalty_manager.py
"""

import pytest
from src.utils.loyalty_manager import calculate_points, calculate_tier, TIER_BRONZE, TIER_SILVER, TIER_GOLD


class TestPointsCalculation:
    def test_floor_applied(self):
        """1 point per £1, floored — £7.99 → 7 pts."""
        assert calculate_points(7.99) == 7

    def test_exact_amount(self):
        """Exact pound amount → same number of points."""
        assert calculate_points(50.00) == 50

    def test_zero_cost(self):
        """Zero cost yields zero points."""
        assert calculate_points(0.00) == 0

    def test_large_booking(self):
        """Large booking is correctly converted."""
        assert calculate_points(123.75) == 123

    def test_less_than_one_pound(self):
        """Sub-£1 costs yield 0 points."""
        assert calculate_points(0.99) == 0


class TestTierAssignment:
    def test_bronze_at_zero(self):
        assert calculate_tier(0) == TIER_BRONZE

    def test_bronze_at_199(self):
        assert calculate_tier(199) == TIER_BRONZE

    def test_silver_at_200(self):
        assert calculate_tier(200) == TIER_SILVER

    def test_silver_at_499(self):
        assert calculate_tier(499) == TIER_SILVER

    def test_gold_at_500(self):
        assert calculate_tier(500) == TIER_GOLD

    def test_gold_above_500(self):
        assert calculate_tier(9999) == TIER_GOLD
