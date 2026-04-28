"""
src/gui/staff_window.py
=======================
Booking Staff dashboard for HCBS — single main window with tabbed areas.
"""
import tkinter as tk

from src.gui.staff_shell_window import StaffShellWindow


class StaffWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        StaffShellWindow(root)
