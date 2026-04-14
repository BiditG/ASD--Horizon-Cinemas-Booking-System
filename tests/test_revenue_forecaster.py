"""
tests/test_revenue_forecaster.py
"""

import pytest
from src.utils.revenue_forecaster import forecast_revenue

def test_forecast_revenue_returns_predictions():
    """Test that the forecasting function returns 3 future month predictions."""
    
    # Using cinema_id 1 which should trigger synthetic data if DB is empty
    actuals_df, predictions = forecast_revenue(1)
    
    assert len(actuals_df) == 6
    assert len(predictions) == 3
    
    # Check predictions format
    for p in predictions:
        assert len(p) == 2
        assert isinstance(p[0], str) # Label e.g. "Jun 2026"
        assert isinstance(p[1], float) # Predicted revenue
        assert p[1] >= 0.0
