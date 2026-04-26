# Student: Simona Kattel, 24030159

#Security-focused tests for HCBS.


from __future__ import annotations

import sqlite3

import pytest

from src.gui.film_listing_window import FilmListingWindow
from src.gui.login_window import SessionManager
from src.models.user import AuthenticationError, User


class MockUser:
    def __init__(self, role: str):
        self.role = role


@pytest.fixture
def security_db():
    """Minimal in-memory DB for auth and user-management security tests."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
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
            last_login TEXT
        );
        """
    )
    return conn


@pytest.fixture(autouse=True)
def clean_session():
    """Ensure each security test starts with no active session."""
    session = SessionManager.get_instance()
    session.clear_session()
    yield
    session.clear_session()


def _seed_user(conn: sqlite3.Connection, username: str = "staff1", password: str = "password123", role: str = "staff") -> None:
    conn.execute(
        """
        INSERT INTO users (cinema_id, username, password_hash, full_name, email, role, theme_pref, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 'dark', 1)
        """,
        (1, username, User.hash_password(password), "Test User", f"{username}@example.com", role),
    )
    conn.commit()


def test_sql_injection_in_login_does_not_bypass_auth(security_db):
    """SQL injection payloads in login fields must not bypass bcrypt auth."""
    _seed_user(security_db)

    with pytest.raises(AuthenticationError):
        User.login("' OR 1=1 --", "anything", security_db)

    with pytest.raises(AuthenticationError):
        User.login("staff1", "' OR 1=1 --", security_db)

    user = User.login("staff1", "password123", security_db)
    assert user.username == "staff1"


def test_authentication_rejects_wrong_password_and_unknown_user(security_db):
    """Wrong passwords and unknown users must both fail cleanly."""
    _seed_user(security_db)

    with pytest.raises(AuthenticationError):
        User.login("staff1", "not_the_password", security_db)

    with pytest.raises(AuthenticationError):
        User.login("missing_user", "password123", security_db)


def test_password_hashing_uses_unique_salts():
    """The same password should hash to different values and still verify."""
    plain = "secure_password"
    hashed_one = User.hash_password(plain)
    hashed_two = User.hash_password(plain)

    assert hashed_one != plain
    assert hashed_two != plain
    assert hashed_one != hashed_two
    assert User.verify_password(plain, hashed_one) is True
    assert User.verify_password(plain, hashed_two) is True


def test_invalid_role_rejected_for_user_creation(monkeypatch, security_db):
    """User creation must reject any role outside the allowed set."""
    monkeypatch.setattr("src.models.user.get_connection", lambda: security_db)

    with pytest.raises(ValueError, match="Invalid role"):
        User.create_user("badrole", "password123", "Bad Role", "bad@example.com", "superadmin")


def test_session_clear_blocks_protected_window(monkeypatch):
    """A cleared session must not be able to open protected staff windows."""
    session = SessionManager.get_instance()
    session.clear_session()

    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    monkeypatch.setattr(messagebox, "showerror", lambda *args, **kwargs: None)

    try:
        FilmListingWindow(root)
        with pytest.raises(tk.TclError):
            root.winfo_exists()
    finally:
        try:
            if root.winfo_exists():
                root.destroy()
        except tk.TclError:
            pass


def test_role_authorization_blocks_unauthenticated_admin_access(monkeypatch):
    """Unauthenticated users must not be able to access admin-only windows."""
    import tkinter as tk
    from tkinter import messagebox
    from src.gui.admin_window import AdminWindow

    session = SessionManager.get_instance()
    session.clear_session()

    root = tk.Tk()
    root.withdraw()
    monkeypatch.setattr(messagebox, "showerror", lambda *args, **kwargs: None)

    try:
        AdminWindow(root)
        with pytest.raises(tk.TclError):
            root.winfo_exists()
    finally:
        try:
            if root.winfo_exists():
                root.destroy()
        except tk.TclError:
            pass


def test_user_object_role_properties_remain_consistent():
    """Role helper properties should reflect the intended privilege model."""
    manager = User(1, 1, "manager1", "hash", "Manager", "m@example.com", "manager")
    admin = User(2, 1, "admin1", "hash", "Admin", "a@example.com", "admin")
    staff = User(3, 1, "staff1", "hash", "Staff", "s@example.com", "staff")

    assert manager.is_manager is True
    assert manager.is_admin is True
    assert manager.is_staff is True
    assert admin.is_manager is False
    assert admin.is_admin is True
    assert staff.is_manager is False
    assert staff.is_admin is False
    assert staff.is_staff is True