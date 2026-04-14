"""
tests/test_noshow_predictor.py
"""

import pytest
import pandas as pd
from src.utils.noshow_predictor import generate_mock_noshow_data, predict_noshow
import os

def test_feature_extraction_logic():
    """Test that the data generator extracts expected feature columns and outputs binary labels."""
    df = generate_mock_noshow_data(100)
    
    expected_cols = {
        "booking_lead_days", "show_time_hour", "day_of_week", 
        "ticket_type", "num_tickets", "cinema_city", "month", "no_show"
    }
    
    assert set(df.columns) == expected_cols
    assert df["no_show"].isin([0, 1]).all()
    assert len(df) == 100

def test_predict_returns_float():
    """Test that predicting a no-show returns a valid probability between 0 and 1."""
    booking_mock = {
        "booking_lead_days": 10,
        "show_time_hour": 19,
        "day_of_week": 5, # Saturday
        "ticket_type": 1,
        "num_tickets": 4,
        "cinema_city": 1,
        "month": 6
    }
    
    prob = predict_noshow(booking_mock)
    
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0
