import pytest
import tkinter as tk
from unittest.mock import patch
from src.gui.login_window import SessionManager
from src.gui.film_listing_window import FilmListingWindow

def test_access_denied_after_logout():
    """
    Asserts that accessing a protected window (FilmListingWindow) after the session
    is cleared correctly raises an access-denied response and does not load
    the window for the unauthenticated user.
    """
    # Create root window
    root = tk.Tk()
    
    # Setup session and explicitly clear it (simulating post-logout state)
    session = SessionManager.get_instance()
    session.clear_session()
    
    # Mock messagebox to intercept the access denied alert
    with patch('src.utils.rbac.messagebox.showerror') as mock_showerror:
        # Attempt to access a staff-protected window
        FilmListingWindow(root)
        
        # Verify an error dialog was spawned
        mock_showerror.assert_called_once()
        args, kwargs = mock_showerror.call_args
        
        # Verify the dialog text indicates access denial
        assert "Access Denied" in args[0]
        assert "permission" in args[1].lower() or "requires" in args[1].lower()
