import datetime
from src.models.booking import BookingManager
from src.models.showing import Showing

class CancellationError(Exception):
    pass

class CancellationManager:
    @staticmethod
    def cancel_booking(booking_ref: str, db_connection) -> dict:
        booking = BookingManager.get_by_ref(booking_ref, db_connection)
        if not booking:
            raise CancellationError("Booking not found")
            
        if booking["booking_status"] == "Cancelled":
            raise CancellationError("Booking is already cancelled")
            
        showing_id = booking["showing_id"]
        showing = Showing.get_by_id(showing_id)
        
        # Validates date rules
        if isinstance(showing.show_date, str):
            show_date = datetime.date.fromisoformat(showing.show_date)
        else:
            show_date = showing.show_date

        today = datetime.date.today()
        diff = (show_date - today).days
        
        if diff < 0:
            raise CancellationError("This show has already passed — no cancellation allowed")
        elif diff == 0:
            raise CancellationError("Same-day cancellation is not permitted — no refund available")
            
        # At least 1 day away -> 50% cancellation fee
        total_cost = booking["total_cost"]
        fee = total_cost * 0.5
        refund_amount = total_cost - fee
        
        now = datetime.datetime.now().isoformat()
        
        try:
            db_connection.execute("BEGIN")
            
            # Update booking status
            db_connection.execute("""
                UPDATE bookings
                SET booking_status = 'Cancelled',
                    cancellation_fee = ?,
                    cancelled_at = ?
                WHERE booking_id = ?
            """, (fee, now, booking["booking_id"]))
            
            qty = len(booking["tickets"])
            Showing.increment_seats(showing_id, qty)
            
            db_connection.commit()
            
            return {
                "booking_ref": booking_ref,
                "cancellation_fee": fee,
                "refund_amount": refund_amount,
                "cancelled_at": now
            }
        except Exception as e:
            db_connection.rollback()
            raise Exception(f"Failed to cancel booking: {e}")
