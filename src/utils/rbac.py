"""
src/utils/rbac.py
=================
Role-Based Access Control (RBAC) utility.
Provides decorators to secure GUI entry points.
"""

from functools import wraps
from tkinter import messagebox
import tkinter as tk
from src.gui.login_window import SessionManager

ROLE_HIERARCHY = {
    'staff': 1,           # Matches 'staff' or 'booking_staff'
    'booking_staff': 1,
    'admin': 2,
    'manager': 3
}

def require_role(minimum_role: str):
    """
    Class decorator to enforce RBAC on Tkinter Window classes.
    Checks the session user's role before running __init__.
    If access is denied, destroys the root window (if Toplevel) and returns early.
    """
    def decorator(cls):
        original_init = cls.__init__
        
        @wraps(original_init)
        def new_init(self, root, *args, **kwargs):
            session = SessionManager.get_instance()
            user = session.get_current_user()
            
            user_role = user.role if user else ''
            user_level = ROLE_HIERARCHY.get(user_role, 0)
            req_level = ROLE_HIERARCHY.get(minimum_role, 99)
            
            if user_level < req_level:
                messagebox.showerror(
                    "Access Denied", 
                    f"You do not have permission to access {cls.__name__}.\nRequires: {minimum_role.capitalize()}"
                )
                if isinstance(root, tk.Toplevel) or isinstance(root, tk.Tk):
                    root.destroy()
                # Return without executing the rest of __init__
                return
                
            original_init(self, root, *args, **kwargs)
            
        cls.__init__ = new_init
        return cls
    return decorator
