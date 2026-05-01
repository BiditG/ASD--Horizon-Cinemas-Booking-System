"""
tests/test_revenue_forecaster.py
"""

import pytest
import sqlite3
import datetime
from src.database import db_connection
import src.database.setup_db as setup_db
from src.utils.revenue_forecaster import forecast_revenue

@pytest.fixture(scope="function")
def db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.isolation_level = None
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    setup_db.create_tables(conn)
    setup_db.seed_data(conn)
    
    original_conn = db_connection._connection
    db_connection._connection = conn
    yield conn
    db_connection._connection = original_conn
    conn.close()

def test_forecast_revenue_returns_predictions(db):
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
