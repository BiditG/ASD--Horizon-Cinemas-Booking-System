import tkinter as tk
from tkinter import messagebox
from typing import Callable, List
from src.database.db_connection import get_connection
from src.utils.seat_recommender import recommend_seats

class SeatMapWindow:
    def __init__(self, parent: tk.Toplevel, showing_id: int, required_quantity: int, ticket_type: str, on_confirm: Callable[[List[str]], None]):
        self.root = tk.Toplevel(parent)
        self.root.title("HCBS — Select Seats")
        self.root.configure(bg="#0f172a")
        
        # Set a reasonable default size and minsize
        self.root.geometry("900x750")
        self.root.minsize(800, 600)
        
        self.root.grab_set() # Make modal
        
        self.showing_id = showing_id
        self.required_quantity = required_quantity
        self.ticket_type = ticket_type
        self.on_confirm = on_confirm
        self.is_bulk = required_quantity >= 10   # Group Booking Mode flag
        
        self.selected_seats = []
        self.seat_buttons = {}
        
        # Load data
        if not self.showing_id:
            messagebox.showerror("Error", "No showing selected.")
            self.root.destroy()
            return

        if not self._load_data():
            return
            
        if self.is_bulk:
            from src.utils.bulk_seat_selector import bulk_select_seats
            selected, max_avail = bulk_select_seats(self.showing_id, self.ticket_type, self.required_quantity)
            if selected is None:
                # Not enough seats — ask to book fewer
                ans = messagebox.askyesno(
                    "Not Enough Seats",
                    f"Not enough seats available for a group of {self.required_quantity}.\n"
                    f"Maximum available: {max_avail}.\n\nWould you like to book {max_avail} instead?",
                    parent=self.root
                )
                if ans and max_avail > 0:
                    self.required_quantity = max_avail
                    selected, _ = bulk_select_seats(self.showing_id, self.ticket_type, self.required_quantity)
                else:
                    self.root.destroy()
                    return
            self.recommended = selected or []
        else:
            self.recommended = recommend_seats(self.showing_id, self.ticket_type, self.required_quantity)
        
        self.is_manual_mode = False
        
        # Build UI
        self._build_ui()
        
        if self.recommended:
            self.selected_seats = list(self.recommended)
            self._update_ui_state()
        else:
            self.is_manual_mode = True
            self.status_lbl.config(text="No recommendations available. Please choose manually.")
            self.confirm_btn.config(text="Confirm Selection")

    def _load_data(self) -> bool:
        try:
            conn = get_connection()
            # Get screen layout
            cursor = conn.execute("""
                SELECT sc.total_capacity, sc.lower_hall_seats, sc.upper_gallery_seats, sc.vip_seats
                FROM showings sh
                JOIN screens sc ON sh.screen_id = sc.screen_id
                WHERE sh.showing_id = ?
            """, (self.showing_id,))
            row = cursor.fetchone()
            if not row:
                messagebox.showerror("Error", "Showing or screen not found.")
                self.root.destroy()
                return False
                
            self.layout = row
            
            # Get booked seats
            cursor = conn.execute("""
                SELECT t.seat_number 
                FROM tickets t
                JOIN bookings b ON t.booking_id = b.booking_id
                WHERE b.showing_id = ? AND b.booking_status = 'Active'
            """, (self.showing_id,))
            self.booked_seats = set(r["seat_number"] for r in cursor.fetchall())
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load seat map: {e}")
            self.root.destroy()
            return False
        
    def _build_ui(self):
        # 1. Main Static Header
        header_frame = tk.Frame(self.root, bg="#0f172a")
        header_frame.pack(fill="x", side="top")

        # Legend
        legend_frame = tk.Frame(header_frame, bg="#0f172a", pady=10)
        legend_frame.pack(fill="x")
        
        tk.Label(legend_frame, text="Legend:", bg="#0f172a", fg="white", font=("Helvetica", 12, "bold")).pack(side="left", padx=10)
        
        self._add_legend_item(legend_frame, "Lower Hall (Free)", "#3b82f6")
        self._add_legend_item(legend_frame, "Lower Hall (Taken)", "#1e40af")
        self._add_legend_item(legend_frame, "Upper Gallery (Free)", "#16a34a")
        self._add_legend_item(legend_frame, "Upper Gallery (Taken)", "#14532d")
        self._add_legend_item(legend_frame, "VIP (Free)", "#ca8a04")
        self._add_legend_item(legend_frame, "VIP (Taken)", "#78350f")
        if self.is_bulk:
            self._add_legend_item(legend_frame, "Group Selection", "#f97316", fg="white")
        else:
            self._add_legend_item(legend_frame, "Recommended/Selected", "yellow", fg="black")
        
        # Status Label — show group booking banner if bulk
        if self.is_bulk:
            tk.Label(header_frame, text=f"🎟 GROUP BOOKING MODE — {self.required_quantity} seats",
                     bg="#f97316", fg="white", font=("Helvetica", 13, "bold"), pady=5).pack(fill="x")
        
        self.status_lbl = tk.Label(header_frame, text=f"0 / {self.required_quantity} seats selected", bg="#0f172a", fg="white", font=("Helvetica", 14))
        self.status_lbl.pack(pady=10)

        # 2. Scrollable Middle Area
        container = tk.Frame(self.root, bg="#0f172a")
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg="#1e293b", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        # This is the frame that actually holds the seats
        self.scrollable_frame = tk.Frame(self.canvas, bg="#1e293b", padx=20, pady=20)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Mousewheel support
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.canvas.create_window((430, 0), window=self.scrollable_frame, anchor="n") # Center the frame in canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 3. Footer Buttons (Static)
        self.btn_frame = tk.Frame(self.root, bg="#0f172a", pady=20)
        self.btn_frame.pack(fill="x", side="bottom")
        
        self.cancel_btn = tk.Button(self.btn_frame, text="Cancel", bg="#334155", fg="white", font=("Helvetica", 12, "bold"), padx=15, command=self.root.destroy)
        self.cancel_btn.pack(side="left", padx=20)
        
        self.manual_btn = tk.Button(self.btn_frame, text="Choose Manually", bg="#f59e0b", fg="black", font=("Helvetica", 12, "bold"), padx=15, command=self._enable_manual)
        
        self.confirm_btn = tk.Button(
            self.btn_frame,
            text="Accept Group Selection" if self.is_bulk else "Accept Recommendation",
            bg="#16a34a", fg="white", font=("Helvetica", 12, "bold"), padx=15, command=self._confirm)
        self.confirm_btn.pack(side="right", padx=20)

        if self.recommended:
            self.manual_btn.pack(side="right", padx=10)

        # 4. Populate Grid (inside scrollable_frame)
        all_seats = []
        for i in range(1, self.layout["lower_hall_seats"] + 1):
            all_seats.append(("lower_hall", f"A{i}"))
        for i in range(1, self.layout["upper_gallery_seats"] + 1):
            all_seats.append(("upper_gallery", f"B{i}"))
        for i in range(1, self.layout["vip_seats"] + 1):
            all_seats.append(("vip", f"V{i}"))
            
        row_idx = 0
        col_idx = 0
        
        for zone, seat_num in all_seats:
            is_booked = seat_num in self.booked_seats
            
            if zone == "lower_hall":
                free_color, taken_color = "#3b82f6", "#1e40af"
            elif zone == "upper_gallery":
                free_color, taken_color = "#16a34a", "#14532d"
            else:
                free_color, taken_color = "#ca8a04", "#78350f"
                
            color = taken_color if is_booked else free_color
            
            btn = tk.Button(self.scrollable_frame, text=seat_num, width=4, height=2, bg=color, fg="white" if not is_booked else "#9ca3af", font=("Helvetica", 10, "bold"), relief="flat")
            if is_booked:
                btn.config(state="disabled")
            else:
                btn.config(command=lambda s=seat_num, c=color: self._toggle_seat(s, c))
                
            btn.grid(row=row_idx, column=col_idx, padx=5, pady=5)
            self.seat_buttons[seat_num] = {"btn": btn, "color": color, "zone": zone}
            
            col_idx += 1
            if col_idx >= 10:
                col_idx = 0
                row_idx += 1

    def _add_legend_item(self, parent, text, color, fg="white"):
        frame = tk.Frame(parent, bg="#0f172a")
        frame.pack(side="left", padx=5)
        tk.Label(frame, bg=color, width=2).pack(side="left")
        tk.Label(frame, text=text, bg="#0f172a", fg=fg, font=("Helvetica", 10)).pack(side="left")

    def _update_ui_state(self):
        # Reset all
        for seat_num, data in self.seat_buttons.items():
            btn = data["btn"]
            color = data["color"]
            if btn["state"] != "disabled":
                btn.config(bg=color, fg="white")
                
        # Color selected
        highlight = "#f97316" if self.is_bulk else "yellow"
        text_col   = "white"   if self.is_bulk else "black"
        for seat_num in self.selected_seats:
            if seat_num in self.seat_buttons:
                self.seat_buttons[seat_num]["btn"].config(bg=highlight, fg=text_col)
                
        self.status_lbl.config(text=f"{len(self.selected_seats)} / {self.required_quantity} seats selected")

    def _enable_manual(self):
        self.is_manual_mode = True
        self.selected_seats = []
        self._update_ui_state()
        self.confirm_btn.config(text="Confirm Selection")
        self.manual_btn.pack_forget()
        
    def _toggle_seat(self, seat_num: str, original_color: str):
        if not self.is_manual_mode:
            # If user clicks a seat while in recommendation mode, switch to manual automatically
            self._enable_manual()
            
        data = self.seat_buttons[seat_num]
        
        if data["zone"] != self.ticket_type:
            messagebox.showwarning("Invalid Zone", f"You must select seats in the {self.ticket_type.replace('_', ' ').title()} zone.")
            return

        if seat_num in self.selected_seats:
            self.selected_seats.remove(seat_num)
        else:
            if len(self.selected_seats) >= self.required_quantity:
                messagebox.showwarning("Limit Reached", f"You can only select {self.required_quantity} seats.")
                return
            self.selected_seats.append(seat_num)
            
        self._update_ui_state()
        
    def _confirm(self):
        if len(self.selected_seats) != self.required_quantity:
            messagebox.showwarning("Incomplete", f"Please select exactly {self.required_quantity} seats.")
            return
            
        # Verify selected seats are in correct zone
        for s in self.selected_seats:
            if self.seat_buttons[s]["zone"] != self.ticket_type:
                messagebox.showerror("Error", f"Seat {s} is not in the correct zone ({self.ticket_type}).")
                return
                
        self.on_confirm(self.selected_seats)
        self.root.destroy()
