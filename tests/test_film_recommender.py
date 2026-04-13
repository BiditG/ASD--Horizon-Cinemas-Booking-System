"""
tests/test_film_recommender.py
"""

import pytest
from unittest.mock import MagicMock, patch
import datetime
from src.utils.film_recommender import recommend_films

@pytest.fixture
def mock_db():
    with patch("src.utils.film_recommender.get_connection") as mock_get_conn:
        conn = MagicMock()
        mock_get_conn.return_value = conn
        yield conn

def test_recommend_films_scoring(mock_db):
    """Test the +3 genre, +2 rating, +1 keyword scoring logic."""
    today = datetime.date.today()
    
    # First call is fetchone() for current film, second is fetchall() for candidates
    # We can mock them based on call order or just set them to MagicMocks
    # The current code calls execute(...).fetchone() then execute(...).fetchall()
    
    mock_cursor_1 = MagicMock()
    mock_cursor_1.fetchone.return_value = {
        "genre": "Action, Sci-Fi",
        "age_rating": "12A"
    }
    
    mock_cursor_2 = MagicMock()
    mock_cursor_2.fetchall.return_value = [
        {
            "film_id": 2, "title": "Exact Match", "genre": "Action, Sci-Fi", "age_rating": "12A",
            "next_show_date": "2026-05-02", "next_show_time": "18:00", "next_showing_id": 10,
            "first_ever_show_date": today.isoformat()
        },
        {
            "film_id": 3, "title": "Genre Only", "genre": "Action, Sci-Fi", "age_rating": "15",
            "next_show_date": "2026-05-02", "next_show_time": "19:00", "next_showing_id": 11,
            "first_ever_show_date": today.isoformat()
        },
        {
            "film_id": 4, "title": "Keyword + Rating", "genre": "Action, Adventure", "age_rating": "12A",
            "next_show_date": "2026-05-02", "next_show_time": "20:00", "next_showing_id": 12,
            "first_ever_show_date": today.isoformat()
        }
    ]
    
    mock_db.execute.side_effect = [mock_cursor_1, mock_cursor_2]
    
    recs = recommend_films(1)
    
    assert len(recs) == 3
    # Exact Match: +3 (genre), +2 (rating), +2 (keywords action, sci-fi) = 7
    # Genre Only: +3 (genre), +0 (rating), +2 (keywords action, sci-fi) = 5
    # Keyword + Rating: +0 (genre diff), +2 (rating), +1 (keyword action) = 3
    
    assert recs[0]["title"] == "Exact Match"
    assert recs[0]["score"] == 7
    assert recs[1]["title"] == "Genre Only"
    assert recs[1]["score"] == 5
    assert recs[2]["title"] == "Keyword + Rating"
    assert recs[2]["score"] == 3

def test_recommend_films_age_penalty(mock_db):
    """Test that older listings are penalized by -1 per day."""
    today = datetime.date.today()
    five_days_ago = (today - datetime.timedelta(days=5)).isoformat()
    
    mock_cursor_1 = MagicMock()
    mock_cursor_1.fetchone.return_value = {
        "genre": "Comedy",
        "age_rating": "PG"
    }
    
    mock_cursor_2 = MagicMock()
    mock_cursor_2.fetchall.return_value = [
        {
            "film_id": 2, "title": "Old Comedy", "genre": "Comedy", "age_rating": "PG",
            "next_show_date": "2026-05-02", "next_show_time": "18:00", "next_showing_id": 10,
            "first_ever_show_date": five_days_ago
        },
        {
            "film_id": 3, "title": "New Comedy", "genre": "Comedy", "age_rating": "PG",
            "next_show_date": "2026-05-02", "next_show_time": "19:00", "next_showing_id": 11,
            "first_ever_show_date": today.isoformat()
        }
    ]
    
    mock_db.execute.side_effect = [mock_cursor_1, mock_cursor_2]
    
    recs = recommend_films(1)
    
    assert len(recs) == 2
    # Both have +3 (genre), +2 (rating), +1 (keyword) = 6 base score
    # Old Comedy has -5 age penalty = 1
    # New Comedy has 0 age penalty = 6
    assert recs[0]["title"] == "New Comedy"
    assert recs[0]["score"] == 6
    assert recs[1]["title"] == "Old Comedy"
    assert recs[1]["score"] == 1
