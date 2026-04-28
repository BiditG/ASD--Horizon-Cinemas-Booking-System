import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.database.db_connection import get_connection


def _safe_p(text) -> str:
    return escape(str(text)) if text is not None else ""


class PDFService:
    @staticmethod
    def generate_ticket(booking_data: dict, output_path: str = None) -> str:
        """
        Generates an A5 PDF ticket for the booking, embeds a QR code, saves it,
        and updates the 'pdf_path' in the tickets database table.
        Mirrors the on-screen receipt (all fields, loyalty when present, full text wrap).
        """
        ref = booking_data.get('booking_ref', 'UNKNOWN')

        if not output_path:
            out_dir = "tickets"
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            output_path = os.path.join(out_dir, f"{ref}.pdf")

        try:
            margin = 14 * mm
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A5,
                leftMargin=margin,
                rightMargin=margin,
                topMargin=margin,
                bottomMargin=margin,
            )
            styles = getSampleStyleSheet()
            title = ParagraphStyle(
                name="ReceiptTitle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=18,
                leading=22,
                alignment=TA_CENTER,
                spaceAfter=4,
            )
            subtitle = ParagraphStyle(
                name="ReceiptSub",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=11,
                leading=14,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#333333"),
                spaceAfter=8,
            )
            confirmed = ParagraphStyle(
                name="Confirmed",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=12,
                leading=15,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#16a34a"),
                spaceBefore=4,
                spaceAfter=10,
            )
            label_style = ParagraphStyle(
                name="ReceiptLabel",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=13,
            )
            value_style = ParagraphStyle(
                name="ReceiptValue",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=13,
            )
            loyalty_style = ParagraphStyle(
                name="LoyaltyLine",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                alignment=TA_CENTER,
                spaceBefore=6,
                spaceAfter=4,
            )
            footer_style = ParagraphStyle(
                name="FooterIt",
                parent=styles["Normal"],
                fontName="Helvetica-Oblique",
                fontSize=9,
                leading=12,
                alignment=TA_CENTER,
                textColor=colors.grey,
                spaceBefore=8,
            )

            seat_numbers = booking_data.get("seat_numbers", [])
            seats_str = (
                ", ".join(seat_numbers)
                if isinstance(seat_numbers, list)
                else str(seat_numbers)
            )
            ticket_type_fmt = (
                booking_data.get("ticket_type", "").replace("_", " ").title()
            )
            total_cost = booking_data.get("total_cost")
            try:
                total_fmt = f"£{float(total_cost):.2f}"
            except (TypeError, ValueError):
                total_fmt = _safe_p(total_cost)

            # Same field order and labels as booking_window.display_receipt
            detail_rows = [
                ("Booking Reference", ref),
                ("Film Name", booking_data.get("film_name", "")),
                ("Show Date", booking_data.get("show_date", "")),
                ("Show Time", booking_data.get("show_time", "")),
                ("Screen Number", str(booking_data.get("screen_id", ""))),
                ("Cinema Name", booking_data.get("cinema_name", "N/A")),
                ("Number of Tickets", str(booking_data.get("quantity", ""))),
                ("Seat Numbers", seats_str),
                ("Ticket Type", ticket_type_fmt),
                ("Booking Date", booking_data.get("booking_date", "")),
                ("Total Cost", total_fmt),
            ]

            usable_w = doc.width
            label_w = 42 * mm
            val_w = usable_w - label_w

            story = []
            story.append(Paragraph(_safe_p("HORIZON CINEMAS"), title))
            story.append(
                Paragraph(_safe_p(booking_data.get("cinema_name", "Cinema")), subtitle)
            )
            story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cccccc")))
            story.append(Spacer(1, 6))
            story.append(Paragraph(_safe_p("BOOKING CONFIRMED"), confirmed))
            story.append(Spacer(1, 4))

            table_data = []
            for lab, val in detail_rows[:-1]:
                table_data.append(
                    [
                        Paragraph(_safe_p(lab), label_style),
                        Paragraph(_safe_p(val), value_style),
                    ]
                )
            lab_last, val_last = detail_rows[-1]
            table_data.append(
                [
                    Paragraph(_safe_p(lab_last), label_style),
                    Paragraph(f"<b><font color='#16a34a'>{_safe_p(val_last)}</font></b>", value_style),
                ]
            )

            tbl = Table(
                table_data,
                colWidths=[label_w, val_w],
                hAlign="LEFT",
            )
            tbl.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#e5e5e5")),
                    ]
                )
            )
            story.append(tbl)

            if "loyalty" in booking_data:
                loy = booking_data["loyalty"]
                tier = str(loy.get("tier", "")).title()
                pts = loy.get("total_points", "")
                earned = loy.get("points_earned", "")
                tier_colors = {
                    "Bronze": "#b45309",
                    "Silver": "#64748b",
                    "Gold": "#d97706",
                }
                tc = tier_colors.get(tier, "#333333")
                line = f"{tier} Member — {pts} pts (+{earned} earned today)"
                story.append(
                    Paragraph(
                        f'<font color="{tc}"><b>{_safe_p(line)}</b></font>',
                        loyalty_style,
                    )
                )

            story.append(Spacer(1, 10))

            from src.utils.qr_generator import save_qr_to_file

            temp_qr_path = f"temp_qr_{ref}.png"
            save_qr_to_file(ref, temp_qr_path)
            qr_mm = 38 * mm
            story.append(
                Image(
                    temp_qr_path,
                    width=qr_mm,
                    height=qr_mm,
                    hAlign="CENTER",
                )
            )

            story.append(Spacer(1, 6))
            story.append(
                Paragraph(
                    _safe_p(
                        "Please present this ticket at the door. No same-day cancellations."
                    ),
                    footer_style,
                )
            )

            doc.build(story)

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
