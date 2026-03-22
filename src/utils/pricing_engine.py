"""
src/utils/pricing_engine.py
===========================
Tiered pricing system for the Horizon Cinemas Booking System (HCBS).

Author      : [Your Name] — Student ID: [Your Student ID]
Module      : Advanced Software Development
Description : Calculates ticket prices based on city, show time, and seat zone.
"""

import datetime
from typing import Dict, Any

class PricingEngine:
    """
    Handles base prices and zone uplifts.
    
    Rules:
    - Base price (Lower Hall) depends on city and show type.
    - Upper Gallery = Base Price * 1.20
    - VIP = Upper Gallery * 1.20 (i.e. Base Price * 1.44)
    - All prices are rounded to 2 decimal places.
    """

    @staticmethod
    def get_lower_hall_price(city_id: int, show_type: str, db_connection) -> float:
        """
        Query the database for the base (lower hall) price.
        
        Args:
            city_id: FK to cities table.
            show_type: 'morning', 'afternoon', or 'evening'.
            db_connection: sqlite3.Connection object.
            
        Returns:
            float: The current base price.
        """
        cursor = db_connection.execute(
            """
            SELECT lower_hall_price 
            FROM prices 
            WHERE city_id = ? AND show_type = ? 
            ORDER BY effective_from DESC LIMIT 1
            """,
            (city_id, show_type.lower())
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"No price found for city_id={city_id}, show_type={show_type}")
        return float(row["lower_hall_price"])

    @staticmethod
    def calculate_price(city_id: int, show_type: str, ticket_type: str, quantity: int, db_connection) -> Dict[str, Any]:
        """
        Calculate the total price for a given number of tickets.
        
        Args:
            city_id: FK to cities.
            show_type: 'morning', 'afternoon', 'evening'.
            ticket_type: 'lower_hall', 'upper_gallery', or 'vip'.
            quantity: Number of tickets.
            db_connection: Active database connection.
            
        Returns:
            dict: {unit_price: float, total_price: float, ticket_type: str, quantity: int, price_breakdown: str}
        """
        base_price = PricingEngine.get_lower_hall_price(city_id, show_type, db_connection)
        
        ticket_type = ticket_type.lower()
        if ticket_type == 'lower_hall':
            unit = base_price
        elif ticket_type == 'upper_gallery':
            unit = round(base_price * 1.20, 2)
        elif ticket_type == 'vip':
            # VIP is 20% more than upper gallery (base * 1.2 * 1.2)
            unit = round((base_price * 1.20) * 1.20, 2)
        else:
            raise ValueError(f"Invalid ticket_type: {ticket_type}")

        total = round(unit * quantity, 2)
        
        return {
            "unit_price": unit,
            "total_price": total,
            "ticket_type": ticket_type,
            "quantity": quantity,
            "price_breakdown": f"{quantity}x {ticket_type.replace('_', ' ').title()} @ £{unit:.2f} = £{total:.2f}"
        }

    @staticmethod
    def get_price_breakdown(city_id: int, show_type: str, db_connection) -> Dict[str, float]:
        """
        Returns all three tier prices for UI display.
        """
        base_price = PricingEngine.get_lower_hall_price(city_id, show_type, db_connection)
        return {
            "lower_hall": round(base_price, 2),
            "upper_gallery": round(base_price * 1.20, 2),
            "vip": round((base_price * 1.20) * 1.20, 2)
        }

    @staticmethod
    def validate_show_type(show_time: str) -> str:
        """
        Map a time string (HH:MM) or datetime.time object to the correct show_type.
        
        - 08:00 - 11:59 -> morning
        - 12:00 - 16:59 -> afternoon
        - 17:00 - 23:59 -> evening
        
        Args:
            show_time: "HH:MM" string or datetime.time.
            
        Returns:
            str: 'morning', 'afternoon', or 'evening'.
        """
        if isinstance(show_time, str):
            try:
                # Support HH:MM or HH:MM:SS
                t = datetime.time.fromisoformat(show_time)
            except ValueError:
                raise ValueError(f"Invalid time format: {show_time}")
        elif isinstance(show_time, datetime.time):
            t = show_time
        else:
            raise TypeError("show_time must be a string or datetime.time")

        if t.hour < 12:
            return "morning"
        elif t.hour < 17:
            return "afternoon"
        else:
            return "evening"
