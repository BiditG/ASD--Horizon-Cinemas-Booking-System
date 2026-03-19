"""
src/gui/booking_window.py
=========================
Booking window stub for HCBS.
Replace this placeholder with the full implementation.
"""
import tkinter as tk
from tkinter import messagebox

BG = "#0f172a"; FG = "#f8fafc"; ACCENT = "#1e40af"

class BookingWindow:
    def __init__(self, root: tk.Toplevel, showing_id: int) -> None:
        self.root = root
        self.showing_id = showing_id
        self.root.title(f"HCBS — New Booking (Showing #{showing_id})")
        self.root.configure(bg=BG)
        self.root.geometry("900x680")

        tk.Label(self.root, text=f"📋  Booking Screen",
                 font=("Helvetica", 20, "bold"), bg=BG, fg=FG).pack(pady=40)
        tk.Label(self.root, text=f"Showing ID: {showing_id}",
                 font=("Helvetica", 13), bg=BG, fg="#94a3b8").pack()
        tk.Label(self.root, text="Full booking interface coming soon.",
                 font=("Helvetica", 11), bg=BG, fg="#94a3b8").pack(pady=8)

        tk.Button(self.root, text="Close", font=("Helvetica", 11, "bold"),
                  bg=ACCENT, fg=FG, relief="flat", padx=20, pady=8,
                  cursor="hand2", command=self.root.destroy).pack(pady=30)
