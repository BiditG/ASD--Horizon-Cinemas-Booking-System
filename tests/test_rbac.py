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
    
    # Also mock messagebox to avoid popup during tests
    import tkinter.messagebox
    monkeypatch.setattr(tkinter.messagebox, "showerror", MagicMock())
    return dummy

def test_staff_access(mock_session):
    mock_session.set_current_user(MockUser('staff'))
    
    root1 = tk.Tk()
    win1 = MockStaffWindow(root1)
    assert hasattr(win1, 'accessed')
    
    root2 = tk.Tk()
    win2 = MockAdminWindow(root2)
    assert not hasattr(win2, 'accessed')
    
    root3 = tk.Tk()
    win3 = MockManagerWindow(root3)
    assert not hasattr(win3, 'accessed')
    
    for r in [root1, root2, root3]:
        try:
            r.destroy()
        except tk.TclError:
            pass

def test_admin_access(mock_session):
    mock_session.set_current_user(MockUser('admin'))
    
    root1 = tk.Tk()
    win1 = MockStaffWindow(root1)
    assert hasattr(win1, 'accessed')
    
    root2 = tk.Tk()
    win2 = MockAdminWindow(root2)
    assert hasattr(win2, 'accessed')
    
    root3 = tk.Tk()
    win3 = MockManagerWindow(root3)
    assert not hasattr(win3, 'accessed')
    
    for r in [root1, root2, root3]:
        try:
            r.destroy()
        except tk.TclError:
            pass

def test_manager_access(mock_session):
    mock_session.set_current_user(MockUser('manager'))
    
    root1 = tk.Tk()
    win1 = MockStaffWindow(root1)
    assert hasattr(win1, 'accessed')
    
    root2 = tk.Tk()
    win2 = MockAdminWindow(root2)
    assert hasattr(win2, 'accessed')
    
    root3 = tk.Tk()
    win3 = MockManagerWindow(root3)
    assert hasattr(win3, 'accessed')
    
    for r in [root1, root2, root3]:
        try:
            r.destroy()
        except tk.TclError:
            pass

def test_no_session(mock_session):
    mock_session.set_current_user(None)
    
    root1 = tk.Tk()
    win1 = MockStaffWindow(root1)
    assert not hasattr(win1, 'accessed')
    
    try:
        root1.destroy()
    except tk.TclError:
        pass
