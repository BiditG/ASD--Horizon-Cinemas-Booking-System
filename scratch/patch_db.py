import sqlite3
import os

DB_PATH = 'hcbs.db'

def patch_db():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("ALTER TABLE showings ADD COLUMN is_cancelled INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        print("Successfully added 'is_cancelled' column to 'showings' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'is_cancelled' already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    patch_db()
