"""
src/gui/admin_window.py
=======================
Admin dashboard stub for HCBS.
Replace this placeholder with the full implementation.
"""
import tkinter as tk

BG = "#0f172a"; FG = "#f8fafc"; ACCENT = "#1e40af"

class AdminWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("HCBS — Admin Dashboard")
        self.root.configure(bg=BG)
        self.root.geometry("1024x768")

        tk.Label(self.root, text="🎬  Admin Dashboard",
                 font=("Helvetica", 22, "bold"), bg=BG, fg=FG).pack(pady=60)
        tk.Label(self.root, text="Full admin interface coming soon.",
                 font=("Helvetica", 12), bg=BG, fg="#94a3b8").pack()

        tk.Button(self.root, text="Logout", font=("Helvetica", 11, "bold"),
                  bg=ACCENT, fg=FG, relief="flat", padx=20, pady=8,
                  cursor="hand2", command=self._logout).pack(pady=40)

    def _logout(self):
        from src.gui.login_window import _logout_and_return
        _logout_and_return(self.root)
