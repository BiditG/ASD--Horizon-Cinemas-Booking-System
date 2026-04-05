"""
src/gui/manager_window.py
=========================
Student ID: 1234567 | Name: Alex Smith

Manager-specific GUI components for Horizon Cinemas Booking System.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime

from src.database.db_connection import get_connection
from src.utils.session import SessionManager
from src.gui.admin_window import AdminWindow

# Style Guide constants
BG = "#0f172a"
BG2 = "#1e293b"
BG_CARD = "#334155"
ACCENT = "#1e40af"
TEXT = "#f8fafc"
TEXT2 = "#94a3b8"
SUCCESS = "#16a34a"
ERROR = "#dc2626"
BORDER = "#475569"

FONT_H1 = ("Helvetica", 24, "bold")
FONT_H2 = ("Helvetica", 16, "bold")
FONT_BODY = ("Helvetica", 11)
FONT_BTN = ("Helvetica", 11, "bold")

from src.utils.rbac import require_role

@require_role('manager')
class ManagerWindow:
    def __init__(self, root: tk.Toplevel):
        self.root = root
        self.root.title("Manager Dashboard - HCBS")
        self.root.geometry("1100x700")
        self.root.configure(bg=BG)
        
        session = SessionManager.get_instance()
        self.user = session.get_current_user()

            
        self._build_ui()
        self._load_overview()

    def _build_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg=BG2, padx=20, pady=15)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="👔 Manager Dashboard", font=FONT_H1, bg=BG2, fg=TEXT).pack(side="left")
        
        btn_frame = tk.Frame(header_frame, bg=BG2)
        btn_frame.pack(side="right")
        
        tk.Button(btn_frame, text="Switch to Admin View", bg=ACCENT, fg=TEXT, font=FONT_BTN, relief="flat", padx=15, pady=8, cursor="hand2", command=self._open_admin).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Close", bg=BG_CARD, fg=TEXT, font=FONT_BTN, relief="flat", padx=15, pady=8, cursor="hand2", command=self.root.destroy).pack(side="left")
        
        # Notebook
        style = ttk.Style()
        style.theme_use('default')
        style.configure("HCBS.TNotebook", background=BG, borderwidth=0)
        style.configure("HCBS.TNotebook.Tab", background=BG2, foreground=TEXT, font=FONT_BTN, padding=[20, 10])
        style.map("HCBS.TNotebook.Tab", background=[("selected", ACCENT)])
        
        self.notebook = ttk.Notebook(self.root, style="HCBS.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tabs
        self.tab_cinema = tk.Frame(self.notebook, bg=BG)
        self.tab_listing = tk.Frame(self.notebook, bg=BG)
        self.tab_overview = tk.Frame(self.notebook, bg=BG)
        
        self.notebook.add(self.tab_cinema, text="Add New Cinema")
        self.notebook.add(self.tab_listing, text="Add New Listing")
        self.notebook.add(self.tab_overview, text="Cinemas Overview")
        
        self._build_cinema_tab()
        self._build_listing_tab()
        self._build_overview_tab()

    # ---- ADMIN VIEW ----
    def _open_admin(self):
        AdminWindow(tk.Toplevel(self.root))

    # ---- TAB 1: ADD CINEMA ----
    def _build_cinema_tab(self):
        card = tk.Frame(self.tab_cinema, bg=BG_CARD, padx=30, pady=30, highlightbackground=BORDER, highlightthickness=1)
        card.pack(pady=30, padx=50, fill="x")
        
        tk.Label(card, text="Register New Cinema Location", font=FONT_H2, bg=BG_CARD, fg=TEXT).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        
        # City
        tk.Label(card, text="City:", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).grid(row=1, column=0, sticky="w", pady=10)
        self.cinema_city_cb = ttk.Combobox(card, values=["Birmingham", "Bristol", "Cardiff", "London"], font=FONT_BODY, width=30)
        self.cinema_city_cb.grid(row=1, column=1, sticky="w", pady=10)
        
        # Name
        tk.Label(card, text="Cinema Name:", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).grid(row=2, column=0, sticky="w", pady=10)
        self.cinema_name_ent = tk.Entry(card, font=FONT_BODY, bg=BG, fg=TEXT, insertbackground=TEXT, width=32, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.cinema_name_ent.grid(row=2, column=1, sticky="w", pady=10)
        
        # Location
        tk.Label(card, text="Location/Address:", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).grid(row=3, column=0, sticky="w", pady=10)
        self.cinema_loc_ent = tk.Entry(card, font=FONT_BODY, bg=BG, fg=TEXT, insertbackground=TEXT, width=32, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.cinema_loc_ent.grid(row=3, column=1, sticky="w", pady=10)
        
        # Screens Config
        tk.Label(card, text="Auto-Create Screens:", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).grid(row=4, column=0, sticky="w", pady=10)
        self.cinema_screens_spin = ttk.Spinbox(card, from_=1, to=6, font=FONT_BODY, width=5)
        self.cinema_screens_spin.set(3)
        self.cinema_screens_spin.grid(row=4, column=1, sticky="w", pady=10)
        
        tk.Label(card, text="Capacity per Screen (50-120):", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).grid(row=5, column=0, sticky="w", pady=10)
        self.cinema_cap_spin = ttk.Spinbox(card, from_=50, to=120, font=FONT_BODY, width=5)
        self.cinema_cap_spin.set(100)
        self.cinema_cap_spin.grid(row=5, column=1, sticky="w", pady=10)
        
        # Submit
        tk.Button(card, text="Create Cinema", bg=SUCCESS, fg=TEXT, font=FONT_BTN, relief="flat", padx=20, pady=10, cursor="hand2", command=self._submit_cinema).grid(row=6, column=0, columnspan=2, pady=20)

    def _submit_cinema(self):
        city = self.cinema_city_cb.get().strip()
        name = self.cinema_name_ent.get().strip()
        loc = self.cinema_loc_ent.get().strip()
        try:
            screens = int(self.cinema_screens_spin.get())
            capacity = int(self.cinema_cap_spin.get())
        except ValueError:
            messagebox.showerror("Validation Error", "Screens and capacity must be valid numbers.")
            return
            
        if not city or not name or not loc:
            messagebox.showerror("Validation Error", "All text fields are required.")
            return
            
        if not (1 <= screens <= 6):
            messagebox.showerror("Validation Error", "Screens must be between 1 and 6.")
            return
            
        if not (50 <= capacity <= 120):
            messagebox.showerror("Validation Error", "Capacity must be between 50 and 120.")
            return
            
        try:
            conn = get_connection()
            conn.execute("BEGIN")
            
            # Lookup or insert city
            cur = conn.execute("SELECT city_id FROM cities WHERE LOWER(city_name) = ?", (city.lower(),))
            city_row = cur.fetchone()
            if city_row:
                city_id = city_row["city_id"]
            else:
                cur = conn.execute("INSERT INTO cities (city_name) VALUES (?)", (city,))
                city_id = cur.lastrowid
                
            # Insert Cinema
            try:
                cur = conn.execute("INSERT INTO cinemas (city_id, cinema_name, location) VALUES (?, ?, ?)", (city_id, name, loc))
            except sqlite3.OperationalError:
                cur = conn.execute("INSERT INTO cinemas (city_id, cinema_name) VALUES (?, ?)", (city_id, name))
                
            cinema_id = cur.lastrowid
            
            # Insert Screens automatically
            lower = int(capacity * 0.6)
            upper = int(capacity * 0.3)
            vip = capacity - lower - upper
            
            for i in range(1, screens + 1):
                conn.execute(
                    "INSERT INTO screens (cinema_id, screen_number, total_capacity, lower_hall_seats, upper_gallery_seats, vip_seats) VALUES (?, ?, ?, ?, ?, ?)",
                    (cinema_id, i, capacity, lower, upper, vip)
                )
                
            conn.commit()
            messagebox.showinfo("Success", f"Cinema '{name}' in {city} created successfully with {screens} screens!")
            
            # Clear form & refresh
            self.cinema_name_ent.delete(0, tk.END)
            self.cinema_loc_ent.delete(0, tk.END)
            self._load_overview()
            self._load_listing_data()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Database Error", f"Failed to add cinema:\n{e}")

    # ---- TAB 2: ADD LISTING ----
    def _build_listing_tab(self):
        card = tk.Frame(self.tab_listing, bg=BG_CARD, padx=30, pady=30, highlightbackground=BORDER, highlightthickness=1)
        card.pack(pady=30, padx=50, fill="x")
        
        tk.Label(card, text="Create Film Listing", font=FONT_H2, bg=BG_CARD, fg=TEXT).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 20))
        
        # Row 1
        tk.Label(card, text="Cinema:", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).grid(row=1, column=0, sticky="w", pady=10)
        self.list_cinema_cb = ttk.Combobox(card, state="readonly", font=FONT_BODY, width=25)
        self.list_cinema_cb.grid(row=1, column=1, sticky="w", pady=10, padx=(0, 20))
        self.list_cinema_cb.bind("<<ComboboxSelected>>", self._on_list_cinema_change)
        
        tk.Label(card, text="Film:", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).grid(row=1, column=2, sticky="w", pady=10)
        self.list_film_cb = ttk.Combobox(card, state="readonly", font=FONT_BODY, width=25)
        self.list_film_cb.grid(row=1, column=3, sticky="w", pady=10)
        
        # Row 2
        tk.Label(card, text="Screen:", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).grid(row=2, column=0, sticky="w", pady=10)
        self.list_screen_cb = ttk.Combobox(card, state="readonly", font=FONT_BODY, width=25)
        self.list_screen_cb.grid(row=2, column=1, sticky="w", pady=10, padx=(0, 20))
        
        tk.Label(card, text="Date (YYYY-MM-DD):", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).grid(row=2, column=2, sticky="w", pady=10)
        self.list_date_ent = tk.Entry(card, font=FONT_BODY, bg=BG, fg=TEXT, insertbackground=TEXT, width=27, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.list_date_ent.grid(row=2, column=3, sticky="w", pady=10)
        self.list_date_ent.insert(0, datetime.date.today().isoformat())
        
        # Row 3: Times
        tk.Label(card, text="Show Times (Comma separated, max 3):", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).grid(row=3, column=0, columnspan=2, sticky="w", pady=10)
        self.list_times_ent = tk.Entry(card, font=FONT_BODY, bg=BG, fg=TEXT, insertbackground=TEXT, width=30, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.list_times_ent.grid(row=3, column=2, columnspan=2, sticky="w", pady=10)
        self.list_times_ent.insert(0, "10:00, 14:00, 19:00")
        
        # Row 4: Pricing Setup
        tk.Label(card, text="Pricing (Lower Hall base):", font=FONT_H2, bg=BG_CARD, fg=TEXT).grid(row=4, column=0, columnspan=4, sticky="w", pady=(20, 10))
        
        price_frame = tk.Frame(card, bg=BG_CARD)
        price_frame.grid(row=5, column=0, columnspan=4, sticky="w")
        
        tk.Label(price_frame, text="Morning (£):", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).pack(side="left")
        self.p_morn_ent = tk.Entry(price_frame, font=FONT_BODY, bg=BG, fg=TEXT, width=8, insertbackground=TEXT, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.p_morn_ent.pack(side="left", padx=(5, 15))
        self.p_morn_ent.insert(0, "5.00")
        
        tk.Label(price_frame, text="Afternoon (£):", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).pack(side="left")
        self.p_aft_ent = tk.Entry(price_frame, font=FONT_BODY, bg=BG, fg=TEXT, width=8, insertbackground=TEXT, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.p_aft_ent.pack(side="left", padx=(5, 15))
        self.p_aft_ent.insert(0, "7.00")
        
        tk.Label(price_frame, text="Evening (£):", font=FONT_BODY, bg=BG_CARD, fg=TEXT2).pack(side="left")
        self.p_eve_ent = tk.Entry(price_frame, font=FONT_BODY, bg=BG, fg=TEXT, width=8, insertbackground=TEXT, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.p_eve_ent.pack(side="left", padx=(5, 15))
        self.p_eve_ent.insert(0, "10.00")
        
        tk.Button(card, text="Submit Listing", bg=SUCCESS, fg=TEXT, font=FONT_BTN, relief="flat", padx=20, pady=10, cursor="hand2", command=self._submit_listing).grid(row=6, column=0, columnspan=4, pady=20)
        
        self._load_listing_data()

    def _load_listing_data(self):
        try:
            conn = get_connection()
            cur = conn.execute("SELECT cinema_id, cinema_name FROM cinemas ORDER BY cinema_name")
            self._cinemas = cur.fetchall()
            self.list_cinema_cb['values'] = [c["cinema_name"] for c in self._cinemas]
            
            cur = conn.execute("SELECT film_id, title FROM films ORDER BY title")
            self._films = cur.fetchall()
            self.list_film_cb['values'] = [f["title"] for f in self._films]
            
        except Exception as e:
            print(f"Error loading listing form data: {e}")

    def _on_list_cinema_change(self, event=None):
        idx = self.list_cinema_cb.current()
        if idx < 0: return
        cid = self._cinemas[idx]["cinema_id"]
        try:
            conn = get_connection()
            cur = conn.execute("SELECT screen_id, screen_number FROM screens WHERE cinema_id = ? ORDER BY screen_number", (cid,))
            self._screens = cur.fetchall()
            self.list_screen_cb['values'] = [f"Screen {s['screen_number']}" for s in self._screens]
            if self._screens:
                self.list_screen_cb.current(0)
        except Exception as e:
            print(f"Error loading screens: {e}")

    def _submit_listing(self):
        c_idx = self.list_cinema_cb.current()
        f_idx = self.list_film_cb.current()
        s_idx = self.list_screen_cb.current()
        
        if c_idx < 0 or f_idx < 0 or s_idx < 0:
            messagebox.showerror("Error", "Please select Cinema, Film, and Screen.")
            return
            
        cid = self._cinemas[c_idx]["cinema_id"]
        fid = self._films[f_idx]["film_id"]
        sid = self._screens[s_idx]["screen_id"]
        
        date_str = self.list_date_ent.get().strip()
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid Date format. Use YYYY-MM-DD.")
            return
            
        times_raw = self.list_times_ent.get().split(',')
        times = [t.strip() for t in times_raw if t.strip()]
        if not times or len(times) > 3:
            messagebox.showerror("Error", "Please enter 1 to 3 valid show times.")
            return
            
        try:
            pm = float(self.p_morn_ent.get())
            pa = float(self.p_aft_ent.get())
            pe = float(self.p_eve_ent.get())
        except ValueError:
            messagebox.showerror("Error", "Prices must be numbers.")
            return

        try:
            conn = get_connection()
            
            # Validate no overlap
            for t in times:
                cur = conn.execute(
                    "SELECT showing_id FROM showings WHERE screen_id = ? AND show_date = ? AND show_time = ? AND is_cancelled = 0",
                    (sid, date_str, t)
                )
                if cur.fetchone():
                    messagebox.showerror("Overlap Error", f"Time {t} already has a showing on this screen!")
                    return

            conn.execute("BEGIN")
            
            cur = conn.execute("SELECT city_id FROM cinemas WHERE cinema_id = ?", (cid,))
            city_id = cur.fetchone()["city_id"]
            
            today_iso = datetime.date.today().isoformat()
            for stype, price in [("morning", pm), ("afternoon", pa), ("evening", pe)]:
                cur = conn.execute("SELECT price_id FROM prices WHERE city_id = ? AND show_type = ?", (city_id, stype))
                if cur.fetchone():
                    conn.execute("UPDATE prices SET lower_hall_price = ?, effective_from = ? WHERE city_id = ? AND show_type = ?", (price, today_iso, city_id, stype))
                else:
                    conn.execute("INSERT INTO prices (city_id, show_type, lower_hall_price, effective_from) VALUES (?, ?, ?, ?)", (city_id, stype, price, today_iso))
            
            cur = conn.execute("SELECT total_capacity FROM screens WHERE screen_id = ?", (sid,))
            cap = cur.fetchone()["total_capacity"]
            
            # Insert Showings
            for t in times:
                hr = int(t.split(':')[0])
                if hr < 12: show_type = "morning"
                elif hr < 17: show_type = "afternoon"
                else: show_type = "evening"
                
                conn.execute(
                    "INSERT INTO showings (film_id, screen_id, show_date, show_time, show_type, seats_remaining) VALUES (?, ?, ?, ?, ?, ?)",
                    (fid, sid, date_str, t, show_type, cap)
                )
                
            conn.commit()
            messagebox.showinfo("Success", "Listings and prices successfully saved!")
            self._load_overview()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Database Error", str(e))

    # ---- TAB 3: OVERVIEW ----
    def _build_overview_tab(self):
        fr = tk.Frame(self.tab_overview, bg=BG)
        fr.pack(fill="both", expand=True, padx=30, pady=30)
        
        tk.Label(fr, text="Cinemas Overview", font=FONT_H2, bg=BG, fg=TEXT).pack(anchor="w", pady=(0, 10))
        
        style = ttk.Style()
        style.configure("HCBS.Treeview", background=BG_CARD, foreground=TEXT, fieldbackground=BG_CARD, borderwidth=0, font=FONT_BODY, rowheight=30)
        style.configure("HCBS.Treeview.Heading", background=BG2, foreground=TEXT, font=FONT_BTN)
        
        cols = ("city", "cinema", "screens", "listings")
        self.tv = ttk.Treeview(fr, columns=cols, show="headings", style="HCBS.Treeview")
        
        self.tv.heading("city", text="City")
        self.tv.heading("cinema", text="Cinema Name")
        self.tv.heading("screens", text="Screen Count")
        self.tv.heading("listings", text="Active Listings")
        
        self.tv.column("city", width=150)
        self.tv.column("cinema", width=250)
        self.tv.column("screens", width=120, anchor="center")
        self.tv.column("listings", width=120, anchor="center")
        
        scroll = ttk.Scrollbar(fr, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=scroll.set)
        
        self.tv.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        btn_fr = tk.Frame(self.tab_overview, bg=BG)
        btn_fr.pack(fill="x", padx=30, pady=(0, 30))
        tk.Button(btn_fr, text="Refresh Data", bg=BG2, fg=TEXT, font=FONT_BTN, relief="flat", padx=15, pady=8, cursor="hand2", command=self._load_overview).pack(side="right")

    def _load_overview(self):
        for item in self.tv.get_children():
            self.tv.delete(item)
            
        try:
            conn = get_connection()
            query = """
            SELECT c.city_name, cn.cinema_name, 
                   COUNT(DISTINCT s.screen_id) as screen_count, 
                   COUNT(DISTINCT sh.showing_id) as listing_count
            FROM cities c
            JOIN cinemas cn ON c.city_id = cn.city_id
            LEFT JOIN screens s ON cn.cinema_id = s.cinema_id
            LEFT JOIN showings sh ON s.screen_id = sh.screen_id
            GROUP BY cn.cinema_id
            ORDER BY c.city_name, cn.cinema_name
            """
            cur = conn.execute(query)
            for row in cur.fetchall():
                self.tv.insert("", "end", values=(
                    row["city_name"],
                    row["cinema_name"],
                    row["screen_count"],
                    row["listing_count"]
                ))
        except Exception as e:
            print(f"Overview loading error: {e}")

if __name__ == "__main__":
    from src.models.user import User
    r = tk.Tk()
    r.withdraw()
    sess = SessionManager.get_instance()
    sess.set_current_user(User(1, 1, "manager_mock", "", "Manager User", "", "manager"))
    mw = ManagerWindow(tk.Toplevel(r))
    r.mainloop()
