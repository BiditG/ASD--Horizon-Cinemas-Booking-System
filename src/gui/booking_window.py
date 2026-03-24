"""
src/gui/booking_window.py
=========================
Booking Form GUI for the Horizon Cinemas Booking System (HCBS).

Author      : [Your Name] — Student ID: [Your Student ID]
Module      : Advanced Software Development
Description : Allows staff to book tickets. Features dynamic showing 
              dropdowns, real-time pricing via PricingEngine, and a 
              receipt generator.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import random
import uuid

# ── Project imports ──────────────────────────────────────────────────────────
from src.database.db_connection import get_connection
from src.models.showing import Showing
from src.models.film import Film
from src.models.screen import Screen
from src.models.user import User
from src.utils.pricing_engine import PricingEngine
from src.gui.login_window import SessionManager

# ── Style Constants ──────────────────────────────────────────────────────────
BG          = "#0f172a"
BG2         = "#1e293b"
BG_CARD     = "#162032"
ACCENT      = "#1e40af"
SUCCESS     = "#16a34a"
WARNING     = "#ca8a04"
ERROR       = "#dc2626"
TEXT        = "#f8fafc"
TEXT2       = "#94a3b8"
BORDER      = "#334155"

FF          = "Helvetica"
FONT_H1     = (FF, 20, "bold")
FONT_H2     = (FF, 16, "bold")
FONT_BODY   = (FF, 11)
FONT_LABEL  = (FF, 11, "bold")
FONT_BTN    = (FF, 11, "bold")
FONT_MONO   = ("Courier New", 10)


class BookingWindow:
    def __init__(self, root: tk.Toplevel, showing_id: int = None) -> None:
        self.root = root
        self.session = SessionManager.get_instance()
        self.user = self.session.get_current_user()
        
        self.root.title("HCBS — New Booking")
        self.root.minsize(1050, 720)
        self.root.configure(bg=BG)
        
        # State variables
        self._showing_id_param = showing_id
        self._all_films = []
        self._available_showings = []
        self._selected_showing: Showing = None
        self.confirmed_price = None
        
        self._configure_styles()
        self._build_ui()
        self._initialise_data()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("HCBS.TCombobox", fieldbackground=BG2, background=BG2, 
                        foreground=TEXT, selectbackground=ACCENT, arrowcolor=TEXT)
        style.configure("HCBS.TRadiobutton", background=BG_CARD, foreground=TEXT, 
                        font=FONT_BODY)
        style.map("HCBS.TRadiobutton",
                  background=[('active', BG_CARD)],
                  indicatorcolor=[('selected', ACCENT)])

    # ── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Main container grid
        self.root.columnconfigure(0, weight=6)  # Form area
        self.root.columnconfigure(1, weight=4)  # Receipt area
        self.root.rowconfigure(0, weight=1)
        
        self._build_form_panel()
        self._build_receipt_panel()

    def _build_form_panel(self) -> None:
        form_frame = tk.Frame(self.root, bg=BG, padx=30, pady=30)
        form_frame.grid(row=0, column=0, sticky="nsew")
        
        tk.Label(form_frame, text="🎟️  New Ticket Booking", font=FONT_H1, bg=BG, fg=TEXT).pack(anchor="w", pady=(0, 20))
        
        # 1. Selection Card
        sel_card = tk.Frame(form_frame, bg=BG_CARD, padx=20, pady=20, highlightbackground=BORDER, highlightthickness=1)
        sel_card.pack(fill="x", pady=(0, 20))
        
        # Date
        tk.Label(sel_card, text="Select Date:", font=FONT_LABEL, bg=BG_CARD, fg=TEXT2).grid(row=0, column=0, sticky="w", pady=5)
        self.date_var = tk.StringVar()
        self.date_cb = ttk.Combobox(sel_card, textvariable=self.date_var, state="readonly", width=25, style="HCBS.TCombobox")
        self.date_cb.grid(row=0, column=1, padx=10, pady=5)
        self.date_cb.bind("<<ComboboxSelected>>", self._on_date_or_film_change)
        
        # Film
        tk.Label(sel_card, text="Select Film:", font=FONT_LABEL, bg=BG_CARD, fg=TEXT2).grid(row=1, column=0, sticky="w", pady=5)
        self.film_var = tk.StringVar()
        self.film_cb = ttk.Combobox(sel_card, textvariable=self.film_var, state="readonly", width=40, style="HCBS.TCombobox")
        self.film_cb.grid(row=1, column=1, padx=10, pady=5)
        self.film_cb.bind("<<ComboboxSelected>>", self._on_date_or_film_change)
        
        # Showing
        tk.Label(sel_card, text="Select Showing:", font=FONT_LABEL, bg=BG_CARD, fg=TEXT2).grid(row=2, column=0, sticky="w", pady=5)
        self.showing_var = tk.StringVar()
        self.showing_cb = ttk.Combobox(sel_card, textvariable=self.showing_var, state="readonly", width=40, style="HCBS.TCombobox")
        self.showing_cb.grid(row=2, column=1, padx=10, pady=5)
        self.showing_cb.bind("<<ComboboxSelected>>", self._on_showing_change)

        # 2. Ticket Details Card
        tkt_card = tk.Frame(form_frame, bg=BG_CARD, padx=20, pady=20, highlightbackground=BORDER, highlightthickness=1)
        tkt_card.pack(fill="x", pady=(0, 20))
        
        tk.Label(tkt_card, text="Ticket Type:", font=FONT_LABEL, bg=BG_CARD, fg=TEXT2).grid(row=0, column=0, sticky="w", pady=5)
        
        self.ticket_type_var = tk.StringVar(value="lower_hall")
        ttk.Radiobutton(tkt_card, text="Lower Hall", variable=self.ticket_type_var, value="lower_hall", style="HCBS.TRadiobutton", command=self._reset_check).grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(tkt_card, text="Upper Gallery", variable=self.ticket_type_var, value="upper_gallery", style="HCBS.TRadiobutton", command=self._reset_check).grid(row=0, column=2, sticky="w")
        ttk.Radiobutton(tkt_card, text="VIP", variable=self.ticket_type_var, value="vip", style="HCBS.TRadiobutton", command=self._reset_check).grid(row=0, column=3, sticky="w")
        
        tk.Label(tkt_card, text="Quantity:", font=FONT_LABEL, bg=BG_CARD, fg=TEXT2).grid(row=1, column=0, sticky="w", pady=(15,5))
        self.qty_var = tk.IntVar(value=1)
        self.qty_spin = ttk.Spinbox(tkt_card, from_=1, to=10, textvariable=self.qty_var, width=5, font=FONT_BODY, command=self._reset_check)
        self.qty_spin.grid(row=1, column=1, sticky="w", pady=(15,5))
        # Bind key release to reset check if user types
        self.qty_spin.bind("<KeyRelease>", lambda e: self._reset_check())
        
        # Check Button & Result
        chk_frame = tk.Frame(tkt_card, bg=BG_CARD)
        chk_frame.grid(row=2, column=0, columnspan=4, sticky="w", pady=(20, 0))
        
        tk.Button(chk_frame, text="🔍 Check Availability & Price", font=FONT_BTN, bg=BG2, fg=TEXT, 
                  activebackground=BG, relief="flat", padx=15, pady=6, cursor="hand2", 
                  command=self.check_availability_and_price).pack(side="left")
                  
        self.avail_lbl = tk.Label(chk_frame, text="", font=FONT_LABEL, bg=BG_CARD, fg=WARNING)
        self.avail_lbl.pack(side="left", padx=20)

        # 3. Customer Details Card
        cust_card = tk.Frame(form_frame, bg=BG_CARD, padx=20, pady=20, highlightbackground=BORDER, highlightthickness=1)
        cust_card.pack(fill="x", pady=(0, 20))
        
        tk.Label(cust_card, text="Customer Name:", font=FONT_BODY, bg=BG_CARD, fg=TEXT).grid(row=0, column=0, sticky="w", pady=5)
        self.cust_name_ent = tk.Entry(cust_card, font=FONT_BODY, bg=BG, fg=TEXT, insertbackground=TEXT, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.cust_name_ent.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        tk.Label(cust_card, text="Phone:", font=FONT_BODY, bg=BG_CARD, fg=TEXT).grid(row=1, column=0, sticky="w", pady=5)
        self.cust_phone_ent = tk.Entry(cust_card, font=FONT_BODY, bg=BG, fg=TEXT, insertbackground=TEXT, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.cust_phone_ent.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        tk.Label(cust_card, text="Email:", font=FONT_BODY, bg=BG_CARD, fg=TEXT).grid(row=2, column=0, sticky="w", pady=5)
        self.cust_email_ent = tk.Entry(cust_card, font=FONT_BODY, bg=BG, fg=TEXT, insertbackground=TEXT, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        self.cust_email_ent.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        cust_card.columnconfigure(1, weight=1)
        
        # 4. Action Buttons
        act_frame = tk.Frame(form_frame, bg=BG)
        act_frame.pack(fill="x", pady=(10, 0))
        
        self.book_btn = tk.Button(act_frame, text="✅ Book Now", font=FONT_BTN, bg=SUCCESS, fg=TEXT, 
                                  activebackground="#15803d", relief="flat", padx=20, pady=10, 
                                  cursor="hand2", state="disabled", command=self._process_booking)
        self.book_btn.pack(side="right")
        
        tk.Button(act_frame, text="Main Menu", font=FONT_BTN, bg=BG2, fg=TEXT, 
                  activebackground=BG_CARD, relief="flat", padx=20, pady=10, 
                  cursor="hand2", command=self.root.destroy).pack(side="left")

    def _build_receipt_panel(self) -> None:
        rec_frame = tk.Frame(self.root, bg=BG2, padx=30, pady=30, highlightbackground=BORDER, highlightthickness=1)
        rec_frame.grid(row=0, column=1, sticky="nsew")
        
        tk.Label(rec_frame, text="🧾 Booking Receipt", font=FONT_H2, bg=BG2, fg=TEXT).pack(anchor="w", pady=(0, 20))
        
        self.receipt_text = tk.Text(rec_frame, font=FONT_MONO, bg=BG, fg=TEXT2, relief="flat", 
                                    padx=15, pady=15, state="disabled")
        self.receipt_text.pack(fill="both", expand=True)

    # ── Initialisation & Data Flow ───────────────────────────────────────────

    def _initialise_data(self) -> None:
        """Load dates, films, and handle optional showing_id parameter."""
        # 1. Populate Dates (Today + 7 days)
        today = datetime.date.today()
        dates = [(today + datetime.timedelta(days=i)).isoformat() for i in range(8)]
        self.date_cb['values'] = dates
        
        # 2. Populate Films
        try:
            self._all_films = Film.get_all_active()
            self.film_cb['values'] = [f.title for f in self._all_films]
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to load films:\n{e}")
            
        # 3. Handle showing_id parameter if provided
        if self._showing_id_param:
            try:
                sh = Showing.get_by_id(self._showing_id_param)
                # Set Date
                if sh.show_date in dates:
                    self.date_var.set(sh.show_date)
                else:
                    self.date_cb['values'] = tuple(list(self.date_cb['values']) + [sh.show_date])
                    self.date_var.set(sh.show_date)
                
                # Set Film
                f_title = next((f.title for f in self._all_films if f.film_id == sh.film_id), "")
                self.film_var.set(f_title)
                
                # Load Showings and Select
                self._on_date_or_film_change()
                
                display_str = f"{sh.show_time} ({sh.show_type.title()})"
                if display_str in self.showing_cb['values']:
                    self.showing_var.set(display_str)
                    self._on_showing_change()
                    
                # Lock Date & Film to prevent confusion
                self.date_cb.config(state="disabled")
                self.film_cb.config(state="disabled")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load showing {self._showing_id_param}:\n{e}")
        else:
            self.date_cb.current(0)
            if self._all_films:
                self.film_cb.current(0)
            self._on_date_or_film_change()

    # ── Event Handlers ───────────────────────────────────────────────────────

    def _on_date_or_film_change(self, event=None) -> None:
        """Fetch showings for the selected date and film."""
        self._reset_check()
        
        date_str = self.date_var.get()
        film_title = self.film_var.get()
        if not date_str or not film_title:
            return
            
        film = next((f for f in self._all_films if f.title == film_title), None)
        if not film:
            return
            
        try:
            conn = get_connection()
            # Fetch showings for this film on this date across ALL cinemas
            # Note: A real system might force cinema selection first. For now, 
            # we fetch all showings for the film+date and display cinema ID too.
            cursor = conn.execute(
                """
                SELECT s.*, sc.cinema_id 
                FROM showings s
                JOIN screens sc ON s.screen_id = sc.screen_id
                WHERE s.film_id = ? AND s.show_date = ? AND s.is_cancelled = 0
                ORDER BY s.show_time
                """, 
                (film.film_id, date_str)
            )
            rows = cursor.fetchall()
            self._available_showings = [Showing._from_row(row) for row in rows]
            
            if not self._available_showings:
                self.showing_cb['values'] = ["No showings available"]
                self.showing_var.set("No showings available")
                self._selected_showing = None
            else:
                displays = [f"{s.show_time} ({s.show_type.title()})" for s in self._available_showings]
                self.showing_cb['values'] = displays
                self.showing_cb.current(0)
                self._on_showing_change()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not load showings: {e}")

    def _on_showing_change(self, event=None) -> None:
        self._reset_check()
        idx = self.showing_cb.current()
        if 0 <= idx < len(self._available_showings):
            self._selected_showing = self._available_showings[idx]
        else:
            self._selected_showing = None

    def _reset_check(self) -> None:
        """Disable Book button and clear price text if params change."""
        self.avail_lbl.config(text="", fg=WARNING)
        self.book_btn.config(state="disabled")
        self.confirmed_price = None

    def check_availability_and_price(self) -> None:
        """Calculate price, verify seat availability, and validate show date."""
        self.avail_lbl.config(text="", fg=WARNING)
        self.book_btn.config(state="disabled")
        self.confirmed_price = None

        # 1. Validate inputs
        if not self._selected_showing:
            self.avail_lbl.config(text="❌ Error: Please select a film and showing.", fg=ERROR)
            return
            
        t_type = self.ticket_type_var.get()
        if not t_type:
            self.avail_lbl.config(text="❌ Error: Please select a ticket type.", fg=ERROR)
            return
            
        try:
            qty = self.qty_var.get()
            if qty < 1 or qty > 10:
                raise ValueError
        except (tk.TclError, ValueError):
            self.avail_lbl.config(text="❌ Error: Quantity must be between 1 and 10.", fg=ERROR)
            return

        sh = self._selected_showing

        # 2. Check if showing is in the past
        today = datetime.date.today().isoformat()
        if sh.show_date < today:
            self.avail_lbl.config(text="❌ This showing has already passed.", fg=ERROR)
            self.book_btn.config(state="disabled")
            return

        # 3. Check seat availability
        if not Showing.is_available(sh.showing_id, qty):
            self.avail_lbl.config(text=f"❌ Not enough seats — only {sh.seats_remaining} remaining.", fg=ERROR)
            return

        # 4. Calculate total cost using PricingEngine
        try:
            conn = get_connection()
            self.confirmed_price = PricingEngine.calculate_price(
                city_id=sh.cinema_id, 
                show_type=sh.show_type, 
                ticket_type=t_type, 
                quantity=qty, 
                db_connection=conn
            )
            
            # 5. Display success result
            total_str = f"£{self.confirmed_price['total_price']:.2f}"
            msg = f"✅ {sh.seats_remaining} seats available — Total: {total_str}"
            self.avail_lbl.config(text=msg, fg=SUCCESS)
            
            # 7. Enable Book Now button
            self.book_btn.config(state="normal")
            
        except Exception as e:
            self.avail_lbl.config(text=f"❌ Pricing Error: {str(e)}", fg=ERROR)

    # ── Booking Processing ───────────────────────────────────────────────────

    def _process_booking(self) -> None:
        name = self.cust_name_ent.get().strip()
        if not name:
            messagebox.showwarning("Missing Info", "Customer Name is required.")
            return
            
        if not self._selected_showing or not self.confirmed_price:
            return
            
        qty = self.confirmed_price["quantity"]
        sh = self._selected_showing
        
        # Generate booking ref
        now = datetime.datetime.now()
        ref = f"HCBS-{now.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        try:
            conn = get_connection()
            
            # 1. Decrement seats atomically
            Showing.decrement_seats(sh.showing_id, qty)
            
            # 2. Insert Booking
            cursor = conn.execute(
                """
                INSERT INTO bookings (showing_id, booking_ref, customer_name, total_cost, booking_status, booked_by_agent)
                VALUES (?, ?, ?, ?, 'Active', 0)
                """,
                (sh.showing_id, ref, name, self.confirmed_price["total_price"])
            )
            booking_id = cursor.lastrowid
            
            # 3. Generate and Insert Tickets
            ttype = self.confirmed_price["ticket_type"]
            uprice = self.confirmed_price["unit_price"]
            prefix = {"lower_hall": "LH", "upper_gallery": "UG", "vip": "VP"}.get(ttype, "T")
            
            seat_numbers = []
            for i in range(qty):
                seat = f"{prefix}-{random.randint(1, 100)}"
                seat_numbers.append(seat)
                conn.execute(
                    """
                    INSERT INTO tickets (booking_id, seat_number, ticket_type, unit_price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (booking_id, seat, ttype, uprice)
                )
            
            conn.commit()
            
            # Refresh local showing data
            sh.seats_remaining -= qty
            
            self._print_receipt(ref, sh, name, qty, seat_numbers, self.confirmed_price["total_price"], now)
            
            messagebox.showinfo("Success", f"Booking Confirmed!\nReference: {ref}")
            self._reset_form()
            
        except Exception as e:
            messagebox.showerror("Booking Failed", str(e))

    def _print_receipt(self, ref: str, sh: Showing, customer: str, qty: int, seats: list, total: float, dt: datetime.datetime) -> None:
        """Render receipt to the text widget."""
        film_title = self.film_var.get()
        screen_id = sh.screen_id # In a real app we'd fetch the actual Screen object
        
        receipt = f"""
========================================
    HORIZON CINEMAS BOOKING SYSTEM
========================================

BOOKING REFERENCE : {ref}
DATE ISSUED       : {dt.strftime('%d %b %Y %H:%M')}

----------------------------------------
CUSTOMER DETAILS
Name              : {customer}

FILM DETAILS
Film Name         : {film_title}
Date              : {sh.show_date}
Show Time         : {sh.show_time} ({sh.show_type.title()})
Screen Number     : {screen_id}

TICKET DETAILS
Number of Tickets : {qty}
Ticket Type       : {self.confirmed_price['ticket_type'].replace('_', ' ').title()}
Seat Numbers      : {', '.join(seats)}

----------------------------------------
TOTAL COST        : £{total:.2f}
========================================
        """
        
        self.receipt_text.config(state="normal")
        self.receipt_text.delete(1.0, tk.END)
        self.receipt_text.insert(tk.END, receipt.strip())
        self.receipt_text.config(state="disabled")

    def _reset_form(self) -> None:
        """Clear customer fields and reset checks after booking."""
        self.cust_name_ent.delete(0, tk.END)
        self.cust_phone_ent.delete(0, tk.END)
        self.cust_email_ent.delete(0, tk.END)
        self.qty_var.set(1)
        self._reset_check()


# ── Standalone launch (for isolated testing) ─────────────────────────────────

if __name__ == "__main__":
    session = SessionManager.get_instance()
    dummy = User(1, None, "test", "", "Test Staff", "", "staff")
    session.set_current_user(dummy)

    root = tk.Tk()
    # Mock launch - pass showing_id=1 to test pre-fill, or None
    BookingWindow(tk.Toplevel(root), showing_id=None)
    root.withdraw()
    root.mainloop()
