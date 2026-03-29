"""
src/gui/film_listing_window.py
==============================
Film Listing screen for the Horizon Cinemas Booking System (HCBS).

Author      : [Your Name] — Student ID: [Your Student ID]
Module      : Advanced Software Development
Description : Displays films and showings for a selected cinema and date.
              Staff can browse by date and click a showing button to proceed
              to the BookingWindow.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import os

# Poster loading utility
from src.utils.image_loader import load_poster

# ── Project imports ──────────────────────────────────────────────────────────
import sys
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.models.cinema  import Cinema
from src.models.showing import Showing
from src.models.film    import Film
from src.gui.login_window import SessionManager

# ── Colour / font constants (matches GUI_STYLE_GUIDE.md) ────────────────────
BG          = "#0f172a"
BG2         = "#1e293b"
BG_CARD     = "#162032"
ACCENT      = "#1e40af"
ACCENT_HVR  = "#1e3a8a"
SUCCESS     = "#16a34a"
SUCCESS_HVR = "#15803d"
SOLD_OUT    = "#334155"
WARNING     = "#ca8a04"
TEXT        = "#f8fafc"
TEXT2       = "#94a3b8"
ERROR       = "#dc2626"
BORDER      = "#334155"

FF          = "Helvetica"
FONT_H1     = (FF, 20, "bold")
FONT_H2     = (FF, 14, "bold")
FONT_BODY   = (FF, 11)
FONT_SMALL  = (FF,  9)
FONT_LABEL  = (FF, 11, "bold")
FONT_BTN    = (FF, 10, "bold")

THUMB_SIZE  = (90, 130)    # poster thumbnail dimensions
CARD_PAD    = 14
CARD_GAP    = 10


class FilmListingWindow:
    """
    Film Listing screen — shown after login for all roles.

    Allows the user to select a cinema and date, then browse all showings
    for that day. Each film card shows poster, metadata, and coloured
    showing-time buttons. Clicking a button routes to BookingWindow.

    Parameters
    ----------
    root : tk.Tk | tk.Toplevel
        The parent Tkinter window.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root    = root
        self.session = SessionManager.get_instance()
        self.user    = self.session.get_current_user()

        self._current_date = datetime.date.today()
        self._cinemas: list[Cinema] = []
        self.poster_images: list    = []   # keep references so GC doesn't collect them
        self._selected_cinema_id: int | None = None

        # Filter state — populated by _refresh_films(), filtered by _apply_filters()
        self._all_films: list[tuple]    = []   # list of (Film, list[Showing])
        self._displayed_films: list[tuple] = []

        # StringVar traces for real-time filtering
        self._search_var    = tk.StringVar()
        self._genre_var     = tk.StringVar(value="All")
        self._rating_var    = tk.StringVar(value="All")

        self._configure_root()
        self._build_ui()
        self._load_cinemas()

    # ── Window setup ─────────────────────────────────────────────────────────

    def _configure_root(self) -> None:
        self.root.title("HCBS — Now Showing")
        self.root.minsize(1024, 768)
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_topbar()
        self._build_controls()
        self._build_search_bar()
        self._build_film_area()
        self._build_statusbar()

    def _build_topbar(self) -> None:
        """Top navigation bar with title and logout."""
        bar = tk.Frame(self.root, bg=BG2, pady=10)
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(1, weight=1)

        tk.Label(bar, text="🎬", font=(FF, 20), bg=BG2, fg=ACCENT
                 ).grid(row=0, column=0, padx=(16, 8))
        tk.Label(bar, text="Horizon Cinemas Booking System",
                 font=FONT_H2, bg=BG2, fg=TEXT
                 ).grid(row=0, column=1, sticky="w")

        # User info
        user_text = f"{self.user.full_name}  ({self.user.role.capitalize()})" if self.user else ""
        tk.Label(bar, text=user_text, font=FONT_SMALL, bg=BG2, fg=TEXT2
                 ).grid(row=0, column=2, padx=12)

        # Cancel Booking
        cancel_btn = tk.Button(
            bar, text="Cancel Booking", font=FONT_BTN,
            bg="#dc2626", fg=TEXT, activebackground="#b91c1c",
            relief="flat", cursor="hand2", padx=14, pady=4,
            command=self._open_cancellation
        )
        cancel_btn.grid(row=0, column=3, padx=(0, 16))

        # Logout
        logout_btn = tk.Button(
            bar, text="Logout", font=FONT_BTN,
            bg=ERROR, fg=TEXT, activebackground="#b91c1c",
            relief="flat", cursor="hand2", padx=14, pady=4,
            command=self._logout
        )
        logout_btn.grid(row=0, column=4, padx=(0, 16))

    def _open_cancellation(self) -> None:
        from src.gui.cancellation_window import CancellationWindow
        CancellationWindow(self.root)

    def _build_controls(self) -> None:
        """Date navigator + cinema selector row."""
        ctrl = tk.Frame(self.root, bg=BG, pady=12)
        ctrl.grid(row=1, column=0, sticky="ew", padx=20)
        ctrl.columnconfigure(3, weight=1)

        # ── Previous / Next day ───────────────────────────────────────────────
        prev_btn = tk.Button(
            ctrl, text="◀  Prev Day", font=FONT_BTN,
            bg=BG2, fg=TEXT, activebackground=ACCENT, relief="flat",
            cursor="hand2", padx=12, pady=6,
            command=self._prev_day
        )
        prev_btn.grid(row=0, column=0, padx=(0, 8))

        self._date_lbl = tk.Label(
            ctrl, text=self._fmt_date(), font=FONT_H2,
            bg=BG, fg=TEXT, width=22, anchor="center"
        )
        self._date_lbl.grid(row=0, column=1)

        next_btn = tk.Button(
            ctrl, text="Next Day  ▶", font=FONT_BTN,
            bg=BG2, fg=TEXT, activebackground=ACCENT, relief="flat",
            cursor="hand2", padx=12, pady=6,
            command=self._next_day
        )
        next_btn.grid(row=0, column=2, padx=(8, 24))

        # ── Cinema selector ───────────────────────────────────────────────────
        tk.Label(ctrl, text="Cinema:", font=FONT_LABEL,
                 bg=BG, fg=TEXT2).grid(row=0, column=3, sticky="e")

        self._cinema_var = tk.StringVar()
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("HCBS.TCombobox",
                        fieldbackground=BG2, background=BG2,
                        foreground=TEXT, selectbackground=ACCENT,
                        arrowcolor=TEXT)
        self._cinema_cb = ttk.Combobox(
            ctrl, textvariable=self._cinema_var,
            state="readonly", font=FONT_BODY, width=34,
            style="HCBS.TCombobox"
        )
        self._cinema_cb.grid(row=0, column=4, padx=(8, 0))
        self._cinema_cb.bind("<<ComboboxSelected>>", self._on_cinema_change)

    def _build_search_bar(self) -> None:
        """
        Search + filter bar — inserted between date controls and film canvas.

        Controls
        --------
        - Search Entry  : real-time title / actor keyword filter (StringVar trace).
        - Genre combo   : filters by exact genre match (or 'All').
        - Age Rating    : filters by exact BBFC rating (or 'All').
        - Clear button  : resets all three controls and re-renders all films.
        """
        GENRES  = ["All", "Action", "Animation", "Comedy", "Documentary",
                   "Drama", "Horror", "Romance", "Sci-Fi", "Thriller"]
        RATINGS = ["All", "U", "PG", "12", "12A", "15", "18"]

        bar = tk.Frame(self.root, bg=BG2, pady=10)
        bar.grid(row=2, column=0, sticky="ew", padx=0)
        bar.columnconfigure(1, weight=1)   # search field expands

        # ── Search label + entry ──────────────────────────────────────────────
        tk.Label(bar, text="🔍  Search by title or actor:",
                 font=FONT_LABEL, bg=BG2, fg=TEXT2
                 ).grid(row=0, column=0, padx=(16, 6))

        search_entry = tk.Entry(
            bar, textvariable=self._search_var,
            font=FONT_BODY, bg=BG, fg=TEXT,
            insertbackground=TEXT, relief="flat",
            highlightbackground=BORDER, highlightthickness=1,
            highlightcolor=ACCENT
        )
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 16), ipady=6)
        search_entry.bind("<FocusIn>",
                          lambda e: search_entry.config(highlightbackground=ACCENT))
        search_entry.bind("<FocusOut>",
                          lambda e: search_entry.config(highlightbackground=BORDER))

        # ── Genre combo ───────────────────────────────────────────────────────
        tk.Label(bar, text="Genre:", font=FONT_LABEL,
                 bg=BG2, fg=TEXT2).grid(row=0, column=2, padx=(0, 6))

        self._genre_cb = ttk.Combobox(
            bar, textvariable=self._genre_var,
            values=GENRES, state="readonly",
            font=FONT_BODY, width=14, style="HCBS.TCombobox"
        )
        self._genre_cb.grid(row=0, column=3, padx=(0, 16))

        # ── Age rating combo ──────────────────────────────────────────────────
        tk.Label(bar, text="Rating:", font=FONT_LABEL,
                 bg=BG2, fg=TEXT2).grid(row=0, column=4, padx=(0, 6))

        self._rating_cb = ttk.Combobox(
            bar, textvariable=self._rating_var,
            values=RATINGS, state="readonly",
            font=FONT_BODY, width=8, style="HCBS.TCombobox"
        )
        self._rating_cb.grid(row=0, column=5, padx=(0, 16))

        # ── Clear Filters button ──────────────────────────────────────────────
        clear_btn = tk.Button(
            bar, text="✕  Clear Filters", font=FONT_BTN,
            bg=SOLD_OUT, fg=TEXT, activebackground=BG,
            relief="flat", cursor="hand2", padx=12, pady=6,
            command=self._clear_filters
        )
        clear_btn.grid(row=0, column=6, padx=(0, 16))
        clear_btn.bind("<Enter>", lambda e: clear_btn.config(bg=BG))
        clear_btn.bind("<Leave>", lambda e: clear_btn.config(bg=SOLD_OUT))

        # ── Attach traces (fire on every change) ─────────────────────────────
        self._search_var.trace_add("write", lambda *_: self._apply_filters())
        self._genre_var .trace_add("write", lambda *_: self._apply_filters())
        self._rating_var.trace_add("write", lambda *_: self._apply_filters())

    def _build_film_area(self) -> None:
        """Scrollable canvas that holds all film cards."""
        wrapper = tk.Frame(self.root, bg=BG)
        wrapper.grid(row=3, column=0, sticky="nsew", padx=20, pady=(8, 0))
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        self._canvas = tk.Canvas(wrapper, bg=BG, highlightthickness=0)
        self._canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(wrapper, orient="vertical",
                                 command=self._canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._canvas.configure(yscrollcommand=scrollbar.set)

        # Inner frame where all cards live
        self._inner = tk.Frame(self._canvas, bg=BG)
        self._inner_id = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )
        self._inner.bind("<Configure>", self._on_inner_resize)
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        # Mouse-wheel scrolling
        self._canvas.bind_all("<MouseWheel>",
                              lambda e: self._canvas.yview_scroll(
                                  -1 * (e.delta // 120), "units"))

    def _build_statusbar(self) -> None:
        """Bottom status bar."""
        bar = tk.Frame(self.root, bg=BG2, pady=6)
        bar.grid(row=4, column=0, sticky="ew")
        bar.columnconfigure(0, weight=1)

        self._status_lbl = tk.Label(
            bar, text="Select a cinema to view today's films.",
            font=FONT_SMALL, bg=BG2, fg=TEXT2, anchor="w"
        )
        self._status_lbl.grid(row=0, column=0, padx=16, sticky="w")

        tk.Label(bar, text="🟢 Available  🔘 Sold Out",
                 font=FONT_SMALL, bg=BG2, fg=TEXT2
                 ).grid(row=0, column=1, padx=16)

    # ── Canvas resize helpers ─────────────────────────────────────────────────

    def _on_inner_resize(self, _e=None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, event) -> None:
        self._canvas.itemconfig(self._inner_id, width=event.width)

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_cinemas(self) -> None:
        """Populate the cinema combobox from the database."""
        try:
            self._cinemas = Cinema.get_all()
            names = [f"{c.cinema_name}" for c in self._cinemas]
            self._cinema_cb['values'] = names
            if names:
                self._cinema_cb.current(0)
                self._selected_cinema_id = self._cinemas[0].cinema_id
                self._refresh_films()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc), parent=self.root)

    def _refresh_films(self) -> None:
        """
        Query the database for showings, build self._all_films, then apply filters.

        This is the only method that hits the database. All subsequent filtering
        is done client-side via _apply_filters() without a DB round-trip.
        """
        self._all_films.clear()

        if self._selected_cinema_id is None:
            return

        date_str = self._current_date.isoformat()
        try:
            showings = Showing.get_by_cinema_date(
                self._selected_cinema_id, date_str
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self.root)
            return

        # Group showings by film_id, fetch Film objects
        film_showings: dict[int, list[Showing]] = {}
        for sh in showings:
            film_showings.setdefault(sh.film_id, []).append(sh)

        for film_id, film_shows in film_showings.items():
            try:
                film = Film.get_by_id(film_id)
                self._all_films.append((film, film_shows))
            except Exception:
                continue

        # Reset filter widgets to 'All' without triggering another refresh
        # (we only reset on date/cinema change, not on filter change)
        self._apply_filters()

    def _apply_filters(self) -> None:
        """
        Filter self._all_films client-side and re-render the visible cards.

        Reads the current values of search_var, genre_var, and rating_var.
        No database calls are made here — operates purely on the cached list.
        """
        query  = self._search_var.get().strip().lower()
        genre  = self._genre_var.get()
        rating = self._rating_var.get()

        self._displayed_films = []
        for film, film_shows in self._all_films:
            # ── Title / actor search ──────────────────────────────────────────
            if query:
                haystack = (
                    film.title.lower() + " " +
                    film.cast_members.lower() + " " +
                    film.description.lower()
                )
                if query not in haystack:
                    continue
            # ── Genre filter ──────────────────────────────────────────────────
            if genre != "All" and film.genre != genre:
                continue
            # ── Age rating filter ─────────────────────────────────────────────
            if rating != "All" and film.age_rating != rating:
                continue

            self._displayed_films.append((film, film_shows))

        self._render_cards()

    def _render_cards(self) -> None:
        """
        Rebuild the scrollable card list from self._displayed_films.

        Called by _apply_filters() every time a filter control changes.
        """
        # Wipe existing cards
        for widget in self._inner.winfo_children():
            widget.destroy()
        self.poster_images.clear()

        if not self._all_films and self._selected_cinema_id is not None:
            tk.Label(
                self._inner,
                text=f"No showings scheduled for {self._fmt_date()}.",
                font=FONT_H2, bg=BG, fg=TEXT2, pady=60
            ).pack()
            self._set_status(f"0 showings on {self._fmt_date()}.")
            return

        if not self._displayed_films:
            # Films exist but filters excluded them all
            msg_frame = tk.Frame(self._inner, bg=BG)
            msg_frame.pack(fill="x", pady=60)
            tk.Label(
                msg_frame, text="🔍  No films match your search.",
                font=FONT_H2, bg=BG, fg=TEXT2
            ).pack()
            tk.Label(
                msg_frame,
                text="Try adjusting the search term, genre, or age rating filter.",
                font=FONT_SMALL, bg=BG, fg=TEXT2
            ).pack(pady=(4, 0))
            self._set_status(
                f"0 of {len(self._all_films)} film(s) match current filters."
            )
            return

        for i, (film, film_shows) in enumerate(self._displayed_films):
            self._build_film_card(self._inner, film, film_shows, i)

        total_shows = sum(len(s) for _, s in self._displayed_films)
        filtered    = len(self._displayed_films) != len(self._all_films)
        filter_note = (f" (filtered from {len(self._all_films)})"
                       if filtered else "")
        self._set_status(
            f"{len(self._displayed_films)} film(s){filter_note}  ·  "
            f"{total_shows} showing(s) on {self._fmt_date()}  ·  "
            f"{self._get_cinema_name()}"
        )

    def _build_film_card(self, parent, film: Film,
                         showings: list[Showing], index: int) -> None:
        """Render one film card with poster, metadata, and showing buttons."""
        bg = BG_CARD if index % 2 == 0 else BG2

        card = tk.Frame(parent, bg=bg, pady=CARD_PAD, padx=CARD_PAD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=0, pady=(0, CARD_GAP))
        card.columnconfigure(1, weight=1)

        # ── Poster thumbnail ──────────────────────────────────────────────────
        poster_frame = tk.Frame(card, bg=bg, width=THUMB_SIZE[0]+4,
                                height=THUMB_SIZE[1]+4)
        poster_frame.grid(row=0, column=0, rowspan=3, padx=(0, 16),
                          sticky="n", pady=4)
        poster_frame.grid_propagate(False)

        poster_lbl = tk.Label(poster_frame, bg=BG)
        poster_lbl.place(x=0, y=0, width=THUMB_SIZE[0], height=THUMB_SIZE[1])

        photo = load_poster(film.poster_path, size=THUMB_SIZE)
        self.poster_images.append(photo)
        poster_lbl.config(image=photo)

        # ── Title row ─────────────────────────────────────────────────────────
        title_row = tk.Frame(card, bg=bg)
        title_row.grid(row=0, column=1, sticky="ew")
        title_row.columnconfigure(0, weight=1)

        tk.Label(title_row, text=film.title,
                 font=FONT_H2, bg=bg, fg=TEXT, anchor="w"
                 ).grid(row=0, column=0, sticky="w")

        # IMDb badge
        if film.imdb_rating:
            tk.Label(title_row,
                     text=f"⭐ {film.imdb_rating:.1f}",
                     font=FONT_SMALL, bg=WARNING, fg="#0f172a",
                     padx=6, pady=2
                     ).grid(row=0, column=1, padx=(8, 0))

        # Age rating badge
        tk.Label(title_row, text=f" {film.age_rating} ",
                 font=(FF, 9, "bold"), bg=ACCENT, fg=TEXT,
                 padx=4, pady=2
                 ).grid(row=0, column=2, padx=(6, 0))

        # ── Meta row ──────────────────────────────────────────────────────────
        meta = (
            f"🎭 {film.genre}   "
            f"⏱ {film.duration_formatted}   "
            + (f"🎬 {film.cast_members[:60]}{'…' if len(film.cast_members)>60 else ''}"
               if film.cast_members else "")
        )
        tk.Label(card, text=meta, font=FONT_SMALL, bg=bg,
                 fg=TEXT2, anchor="w", wraplength=700, justify="left"
                 ).grid(row=1, column=1, sticky="ew", pady=(2, 4))

        # ── Description ───────────────────────────────────────────────────────
        if film.description:
            tk.Label(card, text=film.description[:200] + ("…" if len(film.description) > 200 else ""),
                     font=FONT_SMALL, bg=bg, fg=TEXT2,
                     anchor="w", wraplength=700, justify="left"
                     ).grid(row=2, column=1, sticky="ew", pady=(0, 8))

        # ── Showing buttons ───────────────────────────────────────────────────
        btn_row = tk.Frame(card, bg=bg)
        btn_row.grid(row=3, column=1, sticky="w", pady=(4, 0))

        tk.Label(btn_row, text="Showings:", font=FONT_LABEL,
                 bg=bg, fg=TEXT2).pack(side="left", padx=(0, 10))

        for sh in sorted(showings, key=lambda s: s.show_time):
            sold_out = sh.is_sold_out or sh.seats_remaining <= 0
            btn_bg   = SOLD_OUT if sold_out else SUCCESS
            btn_fg   = TEXT2    if sold_out else TEXT
            btn_text = f"{sh.show_time}\n{'SOLD OUT' if sold_out else f'{sh.seats_remaining} seats'}"
            state    = "disabled" if sold_out else "normal"

            btn = tk.Button(
                btn_row,
                text=btn_text,
                font=FONT_BTN,
                bg=btn_bg, fg=btn_fg,
                activebackground=SUCCESS_HVR if not sold_out else SOLD_OUT,
                activeforeground=TEXT,
                relief="flat", cursor="hand2" if not sold_out else "",
                padx=14, pady=8, state=state,
                command=lambda s=sh: self._open_booking(s)
            )
            btn.pack(side="left", padx=(0, 8))
            if not sold_out:
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=SUCCESS_HVR))
                btn.bind("<Leave>", lambda e, b=btn, c=btn_bg: b.config(bg=c))

    # ── Event handlers ────────────────────────────────────────────────────────

    def _clear_filters(self) -> None:
        """
        Reset all three filter controls to their default 'All' / empty state
        and re-render all films. Traces will fire automatically after set().
        """
        self._search_var.set("")
        self._genre_var .set("All")
        self._rating_var.set("All")
        # Traces have already called _apply_filters; scroll back to top
        self._canvas.yview_moveto(0)

    def _on_cinema_change(self, _event=None) -> None:
        idx = self._cinema_cb.current()
        if 0 <= idx < len(self._cinemas):
            self._selected_cinema_id = self._cinemas[idx].cinema_id
            self._refresh_films()

    def _prev_day(self) -> None:
        self._current_date -= datetime.timedelta(days=1)
        self._date_lbl.config(text=self._fmt_date())
        self._refresh_films()

    def _next_day(self) -> None:
        self._current_date += datetime.timedelta(days=1)
        self._date_lbl.config(text=self._fmt_date())
        self._refresh_films()

    def _open_booking(self, showing: Showing) -> None:
        """Open the BookingWindow for the selected showing."""
        try:
            from src.gui.booking_window import BookingWindow
            top = tk.Toplevel(self.root)
            BookingWindow(top, showing_id=showing.showing_id)
        except ImportError:
            # BookingWindow not yet implemented — show placeholder
            messagebox.showinfo(
                "Proceed to Booking",
                f"Showing ID: {showing.showing_id}\n"
                f"Date: {showing.show_date}  Time: {showing.show_time}\n"
                f"Seats Available: {showing.seats_remaining}\n\n"
                f"BookingWindow coming soon.",
                parent=self.root
            )

    def _logout(self) -> None:
        from src.gui.login_window import _logout_and_return
        _logout_and_return(self.root)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _fmt_date(self) -> str:
        return self._current_date.strftime("%A, %d %B %Y")

    def _get_cinema_name(self) -> str:
        idx = self._cinema_cb.current()
        if 0 <= idx < len(self._cinemas):
            return self._cinemas[idx].cinema_name
        return ""

    def _set_status(self, msg: str) -> None:
        self._status_lbl.config(text=msg)


# ── Standalone launch (for isolated testing) ─────────────────────────────────

if __name__ == "__main__":
    # Inject a dummy session so the window can be tested without logging in
    from src.models.user import User
    session = SessionManager.get_instance()
    dummy = User(1, None, "test", "", "Test User", "", "staff")
    session.set_current_user(dummy)

    root = tk.Tk()
    FilmListingWindow(root)
    root.mainloop()
