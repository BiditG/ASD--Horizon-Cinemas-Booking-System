"""
src/gui/staff_window.py
=======================
Booking Staff dashboard for HCBS.
Launches directly into the Film Listing screen.
"""
import tkinter as tk
from src.gui.film_listing_window import FilmListingWindow

class StaffWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        FilmListingWindow(root)
