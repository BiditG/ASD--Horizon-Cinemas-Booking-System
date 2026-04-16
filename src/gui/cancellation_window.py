import tkinter as tk
from tkinter import messagebox
from src.database.db_connection import get_connection
from src.models.booking import BookingManager
from src.models.showing import Showing
from src.models.cinema import Cinema
import datetime

from src.utils.rbac import require_role

@require_role('staff')
class CancellationWindow:
    def __init__(self, parent: tk.Toplevel):
        self.root = tk.Toplevel(parent)
        self.root.title("Cancel Booking")
        self.root.geometry("600x500")
        self.root.configure(bg="#0f172a")
        self.root.grab_set()
        
        self.current_booking = None
        self._build_ui()
        
    def _build_ui(self):
        # Top frame: search
        top_frame = tk.Frame(self.root, bg="#1e293b", pady=20, padx=20)
        top_frame.pack(fill="x")
        
        tk.Label(top_frame, text="Booking Reference:", bg="#1e293b", fg="white", font=("Helvetica", 12)).pack(side="left", padx=10)
        self.ref_entry = tk.Entry(top_frame, font=("Helvetica", 12))
        self.ref_entry.pack(side="left", padx=10)
        
        tk.Button(top_frame, text="Find Booking", bg="#3b82f6", fg="white", font=("Helvetica", 10, "bold"), command=self._find_booking).pack(side="left", padx=10)
        
        # Details frame
        self.details_frame = tk.Frame(self.root, bg="#0f172a", pady=20, padx=20)
        self.details_frame.pack(fill="both", expand=True)
        
        self.info_lbl = tk.Label(self.details_frame, text="", bg="#0f172a", fg="white", font=("Helvetica", 11), justify="left", anchor="w")
        self.info_lbl.pack(fill="x")
        
        self.fee_lbl = tk.Label(self.details_frame, text="", bg="#0f172a", fg="yellow", font=("Helvetica", 12, "bold"))
        self.fee_lbl.pack(pady=10)
        
        self.error_lbl = tk.Label(self.details_frame, text="", bg="#0f172a", fg="#dc2626", font=("Helvetica", 12, "bold"))
        self.error_lbl.pack(pady=10)
        
        # Buttons
        btn_frame = tk.Frame(self.root, bg="#0f172a", pady=20)
        btn_frame.pack(side="bottom", fill="x")
        
        tk.Button(btn_frame, text="Go Back", bg="#334155", fg="white", font=("Helvetica", 12, "bold"), command=self.root.destroy).pack(side="left", padx=40)
        self.cancel_btn = tk.Button(btn_frame, text="Confirm Cancellation", bg="#dc2626", fg="white", font=("Helvetica", 12, "bold"), state="disabled", command=self._confirm_cancellation)
        self.cancel_btn.pack(side="right", padx=40)

    def _find_booking(self):
        ref = self.ref_entry.get().strip()
        if not ref:
            messagebox.showwarning("Input Error", "Please enter a booking reference.")
            return
            
        try:
            conn = get_connection()
            booking = BookingManager.get_by_ref(ref, conn)
            if not booking:
                self._clear_details("Booking not found.")
                return
                
            if booking["booking_status"] == "Cancelled":
                self._clear_details("This booking is already cancelled.")
                return
                
            sh = Showing.get_by_id(booking["showing_id"])
            
            cursor = conn.execute("SELECT title FROM films WHERE film_id = ?", (sh.film_id,))
            film_title = cursor.fetchone()["title"]
            
            try:
                cinema = Cinema.get_by_id(sh.cinema_id)
                cinema_name = cinema.cinema_name
            except:
                cinema_name = "Horizon Cinemas"
            
            qty = len(booking["tickets"])
            cost = booking["total_cost"]
            
            info_text = (
                f"Film: {film_title}\n"
                f"Show Date & Time: {sh.show_date} {sh.show_time}\n"
                f"Cinema: {cinema_name} (Screen {sh.screen_id})\n"
                f"Customer Name: {booking['customer_name']}\n"
                f"Number of Tickets: {qty}\n"
                f"Original Total Cost: £{cost:.2f}"
            )
            self.info_lbl.config(text=info_text)
            
            fee = cost * 0.5
            self.fee_lbl.config(text=f"Cancellation fee: £{fee:.2f} (50% of £{cost:.2f})")
            
            if isinstance(sh.show_date, str):
                s_date = datetime.date.fromisoformat(sh.show_date)
            else:
                s_date = sh.show_date
                
            diff = (s_date - datetime.date.today()).days
            
            if diff < 0:
                self.error_lbl.config(text="This show has already passed — no cancellation allowed")
                self.cancel_btn.config(state="disabled")
            elif diff == 0:
                self.error_lbl.config(text="Same-day cancellation is not permitted — no refund available")
                self.cancel_btn.config(state="disabled")
            else:
                self.error_lbl.config(text="")
                self.cancel_btn.config(state="normal")
                
            self.current_booking = booking
            
        except Exception as e:
            self._clear_details(f"Error finding booking: {e}")
            
    def _clear_details(self, msg=""):
        self.info_lbl.config(text="")
        self.fee_lbl.config(text="")
        self.error_lbl.config(text=msg)
        self.cancel_btn.config(state="disabled")
        self.current_booking = None

    def _confirm_cancellation(self):
        if not self.current_booking:
            return
            
        ref = self.current_booking["booking_ref"]
        try:
            conn = get_connection()
            from src.models.cancellation import CancellationManager
            res = CancellationManager.cancel_booking(ref, conn)
            
            # Deduct loyalty points
            try:
                from src.utils.loyalty_manager import deduct_points
                email = self.current_booking.get("customer_email", "")
                if email:
                    deduct_points(email, ref, self.current_booking.get("total_cost", 0))
            except Exception as e:
                print(f"Loyalty deduction error: {e}")
            
            try:
                from src.utils.waitlist_manager import process_waitlist
                process_waitlist(self.current_booking["showing_id"], len(self.current_booking["tickets"]))
            except Exception as e:
                print(f"Waitlist processing error: {e}")
            
            messagebox.showinfo("Success", f"Booking {ref} cancelled successfully.\nRefund amount: £{res['refund_amount']:.2f}")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to cancel booking: {e}")
