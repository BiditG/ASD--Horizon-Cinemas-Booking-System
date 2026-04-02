import sqlite3
import bcrypt
import datetime
import random
import os

DB_PATH = 'hcbs.db'

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_tables(cursor):
    cursor.executescript("""
    DROP TABLE IF EXISTS tickets;
    DROP TABLE IF EXISTS waitlist;
    DROP TABLE IF EXISTS bookings;
    DROP TABLE IF EXISTS agent_logs;
    DROP TABLE IF EXISTS loyalty_points;
    DROP TABLE IF EXISTS prices;
    DROP TABLE IF EXISTS showings;
    DROP TABLE IF EXISTS films;
    DROP TABLE IF EXISTS screens;
    DROP TABLE IF EXISTS cinemas;
    DROP TABLE IF EXISTS cities;
    DROP TABLE IF EXISTS users;

    CREATE TABLE cities (
        city_id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_name TEXT NOT NULL
    );

    CREATE TABLE cinemas (
        cinema_id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER,
        cinema_name TEXT NOT NULL,
        FOREIGN KEY(city_id) REFERENCES cities(city_id)
    );

    CREATE TABLE screens (
        screen_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cinema_id INTEGER,
        screen_number INTEGER NOT NULL,
        total_capacity INTEGER NOT NULL,
        lower_hall_seats INTEGER NOT NULL,
        upper_gallery_seats INTEGER NOT NULL,
        vip_seats INTEGER NOT NULL,
        FOREIGN KEY(cinema_id) REFERENCES cinemas(cinema_id)
    );

    CREATE TABLE films (
        film_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        genre TEXT NOT NULL,
        age_rating TEXT NOT NULL,
        duration_mins INTEGER NOT NULL
    );

    CREATE TABLE showings (
        showing_id INTEGER PRIMARY KEY AUTOINCREMENT,
        film_id INTEGER,
        screen_id INTEGER,
        show_date TEXT NOT NULL,
        show_time TEXT NOT NULL,
        show_type TEXT NOT NULL,
        seats_remaining INTEGER NOT NULL,
        FOREIGN KEY(film_id) REFERENCES films(film_id),
        FOREIGN KEY(screen_id) REFERENCES screens(screen_id)
    );

    CREATE TABLE prices (
        price_id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER,
        show_type TEXT NOT NULL,
        lower_hall_price REAL NOT NULL,
        effective_from TEXT NOT NULL,
        FOREIGN KEY(city_id) REFERENCES cities(city_id)
    );

    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cinema_id INTEGER,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL,
        theme_pref TEXT NOT NULL DEFAULT 'dark',
        is_active INTEGER NOT NULL DEFAULT 1,
        last_login TEXT,
        FOREIGN KEY(cinema_id) REFERENCES cinemas(cinema_id)
    );

    CREATE TABLE bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        showing_id INTEGER,
        booking_ref TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        total_cost REAL NOT NULL,
        booking_status TEXT NOT NULL,
        booked_by_agent BOOLEAN NOT NULL,
        cancellation_fee REAL DEFAULT 0.00,
        cancelled_at TEXT,
        staff_id INTEGER DEFAULT 1,
        booking_time TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(showing_id) REFERENCES showings(showing_id),
        FOREIGN KEY(staff_id) REFERENCES users(user_id)
    );

    CREATE TABLE tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER,
        seat_number TEXT NOT NULL,
        ticket_type TEXT NOT NULL,
        unit_price REAL NOT NULL,
        pdf_path TEXT,
        FOREIGN KEY(booking_id) REFERENCES bookings(booking_id)
    );

    CREATE TABLE waitlist (
        waitlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
        showing_id INTEGER,
        customer_name TEXT NOT NULL,
        contact_info TEXT NOT NULL,
        FOREIGN KEY(showing_id) REFERENCES showings(showing_id)
    );

    CREATE TABLE loyalty_points (
        loyalty_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT UNIQUE NOT NULL,
        points INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE agent_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        tool_input TEXT NOT NULL,
        tool_output TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

def seed_data(cursor):
    # 1. Cities
    cities = ['Birmingham', 'Bristol', 'Cardiff', 'London']
    for city in cities:
        cursor.execute("INSERT INTO cities (city_name) VALUES (?)", (city,))
    
    # 2. Cinemas
    cinemas_data = [
        (1, 'Horizon Birmingham Central'), (1, 'Horizon Birmingham South'),
        (2, 'Horizon Bristol East'), (2, 'Horizon Bristol West'),
        (3, 'Horizon Cardiff Bay'), (3, 'Horizon Cardiff North'),
        (4, 'Horizon London West End'), (4, 'Horizon London Stratford')
    ]
    cursor.executemany("INSERT INTO cinemas (city_id, cinema_name) VALUES (?, ?)", cinemas_data)

    # 3. Screens
    screens_data = []
    for cinema_id in range(1, 9):
        for screen_num in range(1, 4): # 3 screens per cinema
            total = random.randint(50, 120)
            vip = random.randint(5, 10)
            lower = int(total * 0.3)
            upper = total - vip - lower
            screens_data.append((cinema_id, screen_num, total, lower, upper, vip))
    cursor.executemany("""
        INSERT INTO screens (cinema_id, screen_number, total_capacity, lower_hall_seats, upper_gallery_seats, vip_seats)
        VALUES (?, ?, ?, ?, ?, ?)
    """, screens_data)

    # 4. Films
    films_data = [
        ('The Matrix Awakens', 'Sci-Fi', '15', 140),
        ('Inception: Restart', 'Sci-Fi', '12A', 152),
        ('Toy Story 5', 'Animation', 'U', 98),
        ('Avengers: Next Gen', 'Action', '12A', 165),
        ('The Silent Echo', 'Horror', '18', 110),
        ('Love in Paris', 'Romance', 'PG', 105),
        ('Desert Storm', 'Action', '15', 130),
        ('Ocean Planet', 'Documentary', 'U', 85)
    ]
    cursor.executemany("""
        INSERT INTO films (title, genre, age_rating, duration_mins)
        VALUES (?, ?, ?, ?)
    """, films_data)

    # 5. Prices
    today = datetime.date.today().isoformat()
    prices_data = [
        # Birmingham
        (1, 'morning', 5.0, today), (1, 'afternoon', 6.0, today), (1, 'evening', 7.0, today),
        # Bristol
        (2, 'morning', 6.0, today), (2, 'afternoon', 7.0, today), (2, 'evening', 8.0, today),
        # Cardiff
        (3, 'morning', 5.0, today), (3, 'afternoon', 6.0, today), (3, 'evening', 7.0, today),
        # London
        (4, 'morning', 10.0, today), (4, 'afternoon', 11.0, today), (4, 'evening', 12.0, today)
    ]
    cursor.executemany("""
        INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from)
        VALUES (?, ?, ?, ?)
    """, prices_data)

    # 6. Showings (At least 20)
    show_types = [('morning', '10:00'), ('afternoon', '14:30'), ('evening', '19:00')]
    showings_data = []
    base_date = datetime.date.today()
    for i in range(30):
        film_id = random.randint(1, 8)
        screen_id = random.randint(1, 24)
        show_date = (base_date + datetime.timedelta(days=random.randint(0, 14))).isoformat()
        stype, stime = random.choice(show_types)
        
        # Get capacity for screen
        cursor.execute("SELECT total_capacity FROM screens WHERE screen_id=?", (screen_id,))
        capacity = cursor.fetchone()[0]
        
        showings_data.append((film_id, screen_id, show_date, stime, stype, capacity))
        
    cursor.executemany("""
        INSERT INTO showings (film_id, screen_id, show_date, show_time, show_type, seats_remaining)
        VALUES (?, ?, ?, ?, ?, ?)
    """, showings_data)

    # 7. Users (cinema_id, username, password_hash, full_name, email, role, theme_pref, is_active)
    users_data = [
        (None, 'manager1', hash_password('password123'), 'Alice Manager',   'alice@hcbs.com',   'manager', 'dark', 1),
        (1,    'admin1',   hash_password('password123'), 'Bob Admin',        'bob@hcbs.com',     'admin',   'dark', 1),
        (5,    'admin2',   hash_password('password123'), 'Carol Admin',      'carol@hcbs.com',   'admin',   'light',1),
        (2,    'staff1',   hash_password('password123'), 'Dave Staff',       'dave@hcbs.com',    'staff',   'dark', 1),
        (3,    'staff2',   hash_password('password123'), 'Eve Staff',        'eve@hcbs.com',     'staff',   'dark', 1),
        (7,    'staff3',   hash_password('password123'), 'Frank Staff',      'frank@hcbs.com',   'staff',   'light',1),
    ]
    cursor.executemany("""
        INSERT INTO users (cinema_id, username, password_hash, full_name, email, role, theme_pref, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)


    # Add a dummy booking and ticket to ensure tables are working
    cursor.execute("""
        INSERT INTO bookings (showing_id, booking_ref, customer_name, total_cost, booking_status, booked_by_agent)
        VALUES (1, 'HCBS-20260430-0001', 'John Doe', 12.0, 'Active', 0)
    """)
    cursor.execute("""
        INSERT INTO tickets (booking_id, seat_number, ticket_type, unit_price)
        VALUES (1, 'A1', 'lower_hall', 6.0), (1, 'A2', 'lower_hall', 6.0)
    """)
    cursor.execute("INSERT INTO waitlist (showing_id, customer_name, contact_info) VALUES (2, 'Jane Smith', 'jane@example.com')")
    cursor.execute("INSERT INTO loyalty_points (customer_name, points) VALUES ('John Doe', 100)")
    cursor.execute("INSERT INTO agent_logs (session_id, tool_name, tool_input, tool_output) VALUES ('sess_123', 'check_availability', '{\"film\":\"Inception\"}', '{\"available\": true}')")


def main():
    print(f"Creating database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    create_tables(cursor)
    print("Tables created successfully.")

    print("Seeding data (this might take a few seconds due to bcrypt)...")
    seed_data(cursor)
    conn.commit()

    # Print summary
    tables = [
        'cities', 'cinemas', 'screens', 'films', 'showings', 'prices', 
        'users', 'bookings', 'tickets', 'waitlist', 'loyalty_points', 'agent_logs'
    ]
    print("\n--- Setup Summary ---")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table.ljust(15)}: {count} rows")
    print("---------------------")

    conn.close()
    print("\nDatabase setup complete.")

if __name__ == "__main__":
    main()
