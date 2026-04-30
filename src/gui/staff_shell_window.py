"""
Single-window staff UI: shared top bar + tabbed Now Showing / New booking / Cancel booking.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.gui.login_window import SessionManager
from src.gui.film_listing_window import FilmListingWindow
from src.gui.booking_window import BookingWindow
from src.gui.cancellation_window import CancellationWindow

BG = "#0b1220"
BG2 = "#111b2e"
BG_CARD = "#111b2e"
ACCENT = "#4f8cff"
TEXT = "#f8fafc"
TEXT2 = "#a7b4c8"
SUCCESS = "#22c55e"
ERROR = "#ef4444"
WARNING = "#f59e0b"
BORDER = "#26344a"
FF = "Segoe UI"
FONT_H2 = (FF, 14, "bold")
FONT_BTN = (FF, 10, "bold")
FONT_SMALL = (FF, 9)


class StaffShellWindow:
    """One main window with ttk.Notebook for core staff tasks."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.session = SessionManager.get_instance()
        self.user = self.session.get_current_user()

        self.root.title("HCBS — Horizon Cinemas (Staff)")
        self.root.minsize(1024, 768)
        self.root.configure(bg=BG)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._build_topbar()
        self._build_notebook()

    def _create_btn(self, parent, text, bg, command, fg="#FFFFFF", **kwargs):
        """Helper to create a styled button with hover effects."""
        btn = tk.Button(
            parent, text=text, bg=bg, fg=fg,
            relief="flat", font=("Segoe UI Semibold", 10),
            padx=15, pady=8, cursor="hand2",
            activebackground=bg, activeforeground=fg,
            command=command, **kwargs
        )
        try:
            r = int(bg[1:3], 16)
            g = int(bg[3:5], 16)
            b = int(bg[5:7], 16)
            hover_bg = f"#{max(0, r-20):02x}{max(0, g-20):02x}{max(0, b-20):02x}"
        except:
            hover_bg = bg
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    # ── Tabs API used by embedded panels ────────────────────────────────────

    def select_now_tab(self) -> None:
        self._notebook.select(self._tab_now)

    def select_book_tab(self) -> None:
        self._notebook.select(self._tab_book)

    def select_cancel_tab(self) -> None:
        self._notebook.select(self._tab_cancel)

    def open_booking_with_showing(self, showing_id: int) -> None:
        """Switch to New booking and pre-fill from a showing (from film cards)."""
        self._notebook.select(self._tab_book)
        self._booking.load_showing_prefill(showing_id)

    # ── UI ─────────────────────────────────────────────────────────────────

    def _build_topbar(self) -> None:
        bar = tk.Frame(self.root, bg=BG2, pady=10)
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(1, weight=1)

        tk.Label(bar, text="🎬", font=(FF, 20), bg=BG2, fg=ACCENT).grid(
            row=0, column=0, padx=(16, 8)
        )
        tk.Label(
            bar,
            text="Horizon Cinemas Booking System",
            font=FONT_H2,
            bg=BG2,
            fg=TEXT,
        ).grid(row=0, column=1, sticky="w")

        user_text = (
            f"{self.user.full_name}  ({self.user.role.capitalize()})"
            if self.user
            else ""
        )
        tk.Label(bar, text=user_text, font=FONT_SMALL, bg=BG2, fg=TEXT2).grid(
            row=0, column=2, padx=12
        )

        col = 3
        if self.user and self.user.role in ("admin", "manager"):
            self._create_btn(bar, "Admin Dashboard", "#0284C7", self._open_admin).grid(row=0, column=col, padx=(0, 16))
            col += 1
            self._create_btn(bar, "📊 Dashboard", "#0D9488", self._open_dashboard).grid(row=0, column=col, padx=(0, 16))
            col += 1

        if self.user:
            self._create_btn(bar, "Logout", ERROR, self._logout).grid(row=0, column=col, padx=(0, 16))
            col += 1

        if self.user and self.user.role == "manager":
            self._create_btn(bar, "Manager Dashboard", "#7C3AED", self._open_manager).grid(row=0, column=col, padx=(0, 16))
            col += 1

        self._create_btn(bar, "❓ Help", WARNING, self._open_chatbot, fg="#000000").grid(row=0, column=col, padx=(0, 16))

    def _build_notebook(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG, foreground=TEXT2, padding=[14, 10], font=(FF, 11, "bold"))
        style.map("TNotebook.Tab", background=[("selected", ACCENT), ("active", BG2)], foreground=[("selected", "#FFFFFF"), ("active", TEXT)])

        nb = ttk.Notebook(self.root)
        nb.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._notebook = nb

        self._tab_now = tk.Frame(nb, bg=BG)
        self._tab_book = tk.Frame(nb, bg=BG)
        self._tab_cancel = tk.Frame(nb, bg=BG)

        nb.add(self._tab_now, text="  Now showing  ")
        nb.add(self._tab_book, text="  New booking  ")
        nb.add(self._tab_cancel, text="  Cancel booking  ")

        self._tab_now.columnconfigure(0, weight=1)
        self._tab_now.rowconfigure(2, weight=1)  # film list area (embedded layout)
        self._tab_book.columnconfigure(0, weight=1)
        self._tab_book.columnconfigure(1, weight=1)
        self._tab_book.rowconfigure(0, weight=1)
        self._tab_cancel.columnconfigure(0, weight=1)
        self._tab_cancel.rowconfigure(0, weight=1)

        FilmListingWindow(self._tab_now, embedded=True, shell=self)
        self._booking = BookingWindow(
            self._tab_book, embedded=True, shell=self, showing_id=None
        )
        CancellationWindow(self._tab_cancel, embedded=True, shell=self)

    def _open_admin(self) -> None:
        from src.gui.admin_window import AdminWindow

        AdminWindow(tk.Toplevel(self.root))

    def _open_manager(self) -> None:
        from src.gui.manager_window import ManagerWindow

        ManagerWindow(tk.Toplevel(self.root))

    def _open_dashboard(self) -> None:
        from src.gui.dashboard_window import DashboardWindow

        DashboardWindow(tk.Toplevel(self.root))

    def _open_chatbot(self) -> None:
        if (
            not hasattr(self, "chatbot_window")
            or not self.chatbot_window.winfo_exists()
        ):
            from src.gui.chatbot_widget import ChatbotWidget

            self.chatbot_window = ChatbotWidget(self.root)
        else:
            self.chatbot_window.show_widget()

    def _logout(self) -> None:
        from src.gui.login_window import _logout_and_return

        _logout_and_return(self.root)
