"""
Seed today's showings across all cinemas and screens.
Run this to populate the database with showings for today.
"""
import sqlite3
import datetime
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'hcbs.db'))

def seed_todays_showings():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    today = datetime.date.today().isoformat()
    
    # Delete existing showings for today
    cursor.execute("DELETE FROM showings WHERE show_date = ?", (today,))
    print(f"Cleared existing showings for {today}")
    
    # Get all screens
    screens = cursor.execute("SELECT screen_id, cinema_id, total_capacity FROM screens ORDER BY cinema_id, screen_id").fetchall()
    
    # Get all active films
    films = cursor.execute("SELECT film_id FROM films WHERE is_active = 1").fetchall()
    
    if not films:
        print("No active films found. Exiting.")
        conn.close()
        return
    
    # For each screen, create 3 showings (morning, afternoon, evening)
    show_types_times = [
        ("morning", "10:00"),
        ("afternoon", "14:30"),
        ("evening", "19:00")
    ]
    
    count = 0
    film_idx = 0
    
    for screen in screens:
        screen_id = screen["screen_id"]
        capacity = screen["total_capacity"]
        
        for show_type, show_time in show_types_times:
            film = films[film_idx % len(films)]
            film_id = film["film_id"]
            
            cursor.execute("""
            INSERT INTO showings (film_id, screen_id, show_date, show_time, show_type, seats_remaining)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (film_id, screen_id, today, show_time, show_type, capacity))
            
            count += 1
            film_idx += 1
    
    conn.commit()
    print(f"Created {count} showings for {today}")
    
    # Print summary
    for cid in range(1, 9):
        c_count = cursor.execute("""
        SELECT COUNT(*) as c FROM showings s
        JOIN screens sc ON s.screen_id = sc.screen_id
        WHERE sc.cinema_id = ? AND s.show_date = ?
        """, (cid, today)).fetchone()['c']
        
        cname = cursor.execute("SELECT cinema_name FROM cinemas WHERE cinema_id = ?", (cid,)).fetchone()
        if c_count > 0:
            print(f"  Cinema {cid} ({cname['cinema_name']}): {c_count} showings")
    
    conn.close()
    print("\nDone! Restart the app to see the showings.")

if __name__ == "__main__":
    seed_todays_showings()
