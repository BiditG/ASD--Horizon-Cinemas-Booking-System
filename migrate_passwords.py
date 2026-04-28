"""
migrate_passwords.py
====================
One-time migration script to re-hash all existing plain-text or weakly hashed
passwords in the users table using bcrypt.
"""

import sqlite3
import os
from src.models.user import User

def get_db_connection() -> sqlite3.Connection:
    """Connect to the SQLite database."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'hcbs.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_passwords():
    print("Starting password migration...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch all users
        cursor.execute("SELECT user_id, username, password_hash FROM users")
        users = cursor.fetchall()

        migrated_count = 0
        skipped_count = 0

        for user in users:
            user_id = user['user_id']
            username = user['username']
            password_hash = user['password_hash']

            # Check if password is already hashed with bcrypt
            if password_hash.startswith("$2b$"):
                skipped_count += 1
                continue

            # Otherwise, hash it
            new_hash = User.hash_password(password_hash)
            
            # Update the database
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE user_id = ?",
                (new_hash, user_id)
            )
            migrated_count += 1
            print(f"Migrated password for user: {username}")

        conn.commit()
        print(f"Migration complete. Migrated: {migrated_count}, Skipped: {skipped_count}.")

    except Exception as e:
        print(f"An error occurred during migration: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_passwords()
