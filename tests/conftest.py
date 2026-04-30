"""
conftest.py
================
Pytest configuration file for Horizon Cinemas Booking System.
"""

import os
import pytest
import sqlite3

from src.database import db_connection
import src.database.setup_db as setup_db

# Detect if running in CI environment
CI_ENV = os.environ.get('CI') == 'true'

# Export a GUI skip marker that tests can use: @skip_gui_in_ci
skip_gui_in_ci = pytest.mark.skipif(CI_ENV, reason='GUI not available in CI')

# def pytest_html_report_title(report):
#     """Set the custom title of the HTML report."""
#     report.title = "HCBS Portfolio Test Report"

def pytest_configure(config):
    """Add custom metadata to the pytest-html report."""
    try:
        if hasattr(config, '_metadata'):
            config._metadata["Project"] = "Horizon Cinemas Booking System"
            config._metadata["Module"] = "Advanced Software Development"
            config._metadata["Description"] = "Portfolio Submission Evidence"
            config._metadata["Environment"] = "CI" if CI_ENV else "Local"
    except Exception:
        pass

@pytest.fixture(scope="session", autouse=True)
def configure_global_db():
    """
    If running in CI, force the global db_connection to use an in-memory SQLite DB
    to avoid writing files or needing MySQL.
    """
    if CI_ENV:
        conn = sqlite3.connect(':memory:', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        
        setup_db.create_tables(conn)
        setup_db.seed_data(conn)
        
        # Override the application singleton
        db_connection._connection = conn
        yield conn
        conn.close()
    else:
        # Local development uses the standard file DB
        yield db_connection.get_connection()

