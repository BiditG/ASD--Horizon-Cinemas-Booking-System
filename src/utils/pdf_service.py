import os
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from src.database.db_connection import get_connection

class PDFService:
    @staticmethod
    def generate_ticket(booking_data: dict, output_path: str = None) -> str:
        """
        Generates an A5 PDF ticket for the booking, embeds a QR code, saves it,
        and updates the 'pdf_path' in the tickets database table.
        """
        ref = booking_data.get('booking_ref', 'UNKNOWN')
        
        if not output_path:
            out_dir = "tickets"
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            output_path = os.path.join(out_dir, f"{ref}.pdf")
            
        try:
            c = canvas.Canvas(output_path, pagesize=A5)
            width, height = A5
            
            # --- Header ---
            c.setFont("Helvetica-Bold", 24)
            c.drawCentredString(width / 2.0, height - 25*mm, "HORIZON CINEMAS")
            
            c.setFont("Helvetica", 14)
            c.drawCentredString(width / 2.0, height - 35*mm, booking_data.get("cinema_name", "Cinema"))
            
            # --- Divider ---
            c.setLineWidth(1)
            c.line(15*mm, height - 42*mm, width - 15*mm, height - 42*mm)
            
            # --- Details (Two-column) ---
            c.setFont("Helvetica", 11)
            
            seat_numbers = booking_data.get("seat_numbers", [])
            seats_str = ", ".join(seat_numbers) if isinstance(seat_numbers, list) else str(seat_numbers)
            
            fields_left = [
                ("Film:", booking_data.get("film_name", "")),
                ("Date:", booking_data.get("show_date", "")),
                ("Time:", booking_data.get("show_time", "")),
                ("Screen:", str(booking_data.get("screen_id", ""))),
            ]
            
            fields_right = [
                ("Cinema:", booking_data.get("cinema_name", "")),
                ("Ticket Type:", booking_data.get("ticket_type", "").replace('_', ' ').title()),
                ("Seat Numbers:", seats_str),
                ("Customer Name:", booking_data.get("customer_name", "")),
                ("Booking Ref:", ref)
            ]
            
            y_pos = height - 55*mm
            line_height = 8*mm
            
            # Draw left column
            for label, value in fields_left:
                c.setFont("Helvetica-Bold", 11)
                c.drawString(15*mm, y_pos, label)
                c.setFont("Helvetica", 11)
                c.drawString(45*mm, y_pos, str(value))
                y_pos -= line_height
                
            # Draw right column
            y_pos = height - 55*mm
            for label, value in fields_right:
                c.setFont("Helvetica-Bold", 11)
                c.drawString(width/2.0 + 5*mm, y_pos, label)
                c.setFont("Helvetica", 11)
                val_str = str(value)
                if len(val_str) > 25:
                    val_str = val_str[:22] + "..."
                c.drawString(width/2.0 + 35*mm, y_pos, val_str)
                y_pos -= line_height
                
            # --- QR Code ---
            from src.utils.qr_generator import save_qr_to_file
            temp_qr_path = f"temp_qr_{ref}.png"
            save_qr_to_file(ref, temp_qr_path)
            
            # Embed in bottom-right
            qr_size = 40*mm
            c.drawImage(temp_qr_path, width - 15*mm - qr_size, 25*mm, width=qr_size, height=qr_size)
            
            # --- Footer ---
            c.setFont("Helvetica-Oblique", 10)
            c.drawCentredString(width / 2.0, 15*mm, "Please present this ticket at the door. No same-day cancellations.")
            
            c.save()
            
            # Cleanup temp qr
            if os.path.exists(temp_qr_path):
                os.remove(temp_qr_path)
                
            # --- Update DB ---
            try:
                conn = get_connection()
                # Find booking_id using booking_ref
                row = conn.execute("SELECT booking_id FROM bookings WHERE booking_ref = ?", (ref,)).fetchone()
                if row:
                    b_id = row["booking_id"]
                    conn.execute("UPDATE tickets SET pdf_path = ? WHERE booking_id = ?", (output_path, b_id))
                    conn.commit()
            except Exception as db_e:
                print(f"Warning: Failed to update db with pdf path: {db_e}")
                
            return os.path.abspath(output_path)
            
        except Exception as e:
            raise Exception(f"Failed to generate ticket PDF: {e}")
