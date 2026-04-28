"""
src/utils/film_recommender.py
"""

import datetime
from src.database.db_connection import get_connection

def recommend_films(current_film_id: int, cinema_id: int = None) -> list[dict]:
    """
    Recommend up to 3 similar films based on content filtering.
    
    Scoring:
    - +3 points if genre matches exactly
    - +2 points if age_rating matches
    - +1 point per shared genre keyword
    - -1 point for each day the film has been showing
    """
    conn = get_connection()
    today_str = datetime.date.today().isoformat()
    today_dt = datetime.date.today()
    
    # Fetch current film
    curr = conn.execute("SELECT genre, age_rating FROM films WHERE film_id = ?", (current_film_id,)).fetchone()
    if not curr:
        return []
        
    curr_genre = curr["genre"].lower()
    curr_rating = curr["age_rating"]
    curr_keywords = set(k.strip() for k in curr_genre.replace('/', ',').split(',') if k.strip())
    
    params = [today_str, current_film_id]
    cinema_filter = ""
    if cinema_id is not None:
        cinema_filter = " AND s.screen_id IN (SELECT screen_id FROM screens WHERE cinema_id = ?) "
        params.append(cinema_id)
        
    # Find active films with future showings
    query = f"""
        SELECT f.film_id, f.title, f.genre, f.age_rating,
               MIN(s.show_date) as next_show_date,
               MIN(s.show_time) as next_show_time,
               MIN(s.showing_id) as next_showing_id,
               (SELECT MIN(show_date) FROM showings WHERE film_id = f.film_id) as first_ever_show_date
        FROM films f
        JOIN showings s ON f.film_id = s.film_id
        WHERE s.show_date >= ? AND f.film_id != ? AND f.is_active = 1
        {cinema_filter}
        GROUP BY f.film_id
    """
    
    rows = conn.execute(query, params).fetchall()
    
    scored = []
    for r in rows:
        score = 0
        cand_genre = r["genre"].lower()
        
        if cand_genre == curr_genre:
            score += 3
            
        if r["age_rating"] == curr_rating:
            score += 2
            
        cand_keywords = set(k.strip() for k in cand_genre.replace('/', ',').split(',') if k.strip())
        score += len(curr_keywords.intersection(cand_keywords))
        
        if r["first_ever_show_date"]:
            first_dt = datetime.date.fromisoformat(r["first_ever_show_date"])
            days_showing = (today_dt - first_dt).days
            if days_showing > 0:
                score -= days_showing
                
        scored.append({
            "film_id": r["film_id"],
            "title": r["title"],
            "genre": r["genre"],
            "age_rating": r["age_rating"],
            "next_show_date": r["next_show_date"],
            "next_show_time": r["next_show_time"],
            "next_showing_id": r["next_showing_id"],
            "score": score
        })
        
    scored.sort(key=lambda x: (-x["score"], x["title"]))
    return scored[:3]
