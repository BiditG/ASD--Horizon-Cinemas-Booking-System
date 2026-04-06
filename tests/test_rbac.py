"""
tests/test_rbac.py
==================
Unit tests for Role-Based Access Control (RBAC) decorator.
Covers all three roles attempting to access each window tier.
"""

import pytest
import tkinter as tk
from unittest.mock import MagicMock
from src.utils.rbac import require_role
from src.gui.login_window import SessionManager


class MockUser:
    def __init__(self, role):
        self.role = role


# Mock target classes to test the decorators
@require_role('staff')
class MockStaffWindow:
    def __init__(self, root):
        self.accessed = True


@require_role('admin')
class MockAdminWindow:
    def __init__(self, root):
        self.accessed = True


@require_role('manager')
class MockManagerWindow:
    def __init__(self, root):
        self.accessed = True


# ── Module-level Tk root shared across all tests to avoid Tcl teardown issues ─
_root = None

def _get_root():
    """Return a live tk.Tk, creating one only if needed."""
    global _root
    try:
        if _root is None or not _root.winfo_exists():
            raise tk.TclError
        return _root
    except tk.TclError:
        _root = tk.Tk()
        _root.withdraw()
        return _root


def _make_toplevel():
    """Create a Toplevel off the shared root so destroy() is safe."""
    return tk.Toplevel(_get_root())


@pytest.fixture
def mock_session(monkeypatch):
    class DummySession:
        def __init__(self):
            self.user = None
        def get_current_user(self):
            return self.user
        def set_current_user(self, user):
            self.user = user

    dummy = DummySession()
    monkeypatch.setattr(SessionManager, "get_instance", lambda: dummy)

    import tkinter.messagebox
    monkeypatch.setattr(tkinter.messagebox, "showerror", MagicMock())
    return dummy


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_staff_cannot_access_admin_or_manager(mock_session):
    """Booking Staff: can open Staff window, blocked from Admin and Manager."""
    mock_session.set_current_user(MockUser('staff'))

    t1 = _make_toplevel()
    w1 = MockStaffWindow(t1)
    assert hasattr(w1, 'accessed'), "Staff should access Staff window"

    t2 = _make_toplevel()
    w2 = MockAdminWindow(t2)
    assert not hasattr(w2, 'accessed'), "Staff should NOT access Admin window"

    t3 = _make_toplevel()
    w3 = MockManagerWindow(t3)
    assert not hasattr(w3, 'accessed'), "Staff should NOT access Manager window"


def test_admin_cannot_access_manager(mock_session):
    """Admin: can open Staff + Admin windows, blocked from Manager."""
    mock_session.set_current_user(MockUser('admin'))

    t1 = _make_toplevel()
    w1 = MockStaffWindow(t1)
    assert hasattr(w1, 'accessed'), "Admin should access Staff window"

    t2 = _make_toplevel()
    w2 = MockAdminWindow(t2)
    assert hasattr(w2, 'accessed'), "Admin should access Admin window"

    t3 = _make_toplevel()
    w3 = MockManagerWindow(t3)
    assert not hasattr(w3, 'accessed'), "Admin should NOT access Manager window"


def test_manager_can_access_all(mock_session):
    """Manager: can open Staff, Admin, and Manager windows."""
    mock_session.set_current_user(MockUser('manager'))

    t1 = _make_toplevel()
    w1 = MockStaffWindow(t1)
    assert hasattr(w1, 'accessed'), "Manager should access Staff window"

    t2 = _make_toplevel()
    w2 = MockAdminWindow(t2)
    assert hasattr(w2, 'accessed'), "Manager should access Admin window"

    t3 = _make_toplevel()
    w3 = MockManagerWindow(t3)
    assert hasattr(w3, 'accessed'), "Manager should access Manager window"


def test_no_session_blocked_everywhere(mock_session):
    """No authenticated user: all windows denied."""
    mock_session.set_current_user(None)

    t1 = _make_toplevel()
    w1 = MockStaffWindow(t1)
    assert not hasattr(w1, 'accessed'), "Unauthenticated should NOT access any window"

    t2 = _make_toplevel()
    w2 = MockAdminWindow(t2)
    assert not hasattr(w2, 'accessed')

    t3 = _make_toplevel()
    w3 = MockManagerWindow(t3)
    assert not hasattr(w3, 'accessed')


def test_booking_staff_role_alias(mock_session):
    """'booking_staff' string maps to same level as 'staff'."""
    mock_session.set_current_user(MockUser('booking_staff'))

    t1 = _make_toplevel()
    w1 = MockStaffWindow(t1)
    assert hasattr(w1, 'accessed'), "booking_staff should access Staff window"

    t2 = _make_toplevel()
    w2 = MockAdminWindow(t2)
    assert not hasattr(w2, 'accessed'), "booking_staff should NOT access Admin window"
