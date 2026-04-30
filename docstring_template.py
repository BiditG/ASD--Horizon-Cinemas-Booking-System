"""
docstring_template.py
=====================
This file defines the project's agreed docstring standard for the
Horizon Cinemas Booking System (HCBS) portfolio submission.

Standard: Google Style / Sphinx compliant docstrings.
Every class, module, and non-trivial function must have a docstring
matching this exact format to ensure clean documentation generation
and consistent team code style.
"""

def calculate_ticket_price(base_price: float, ticket_type: str, city: str) -> float:
    """
    Calculate the final ticket price based on type and city.

    Args:
        base_price (float): The base lower hall price for the city/time band.
        ticket_type (str): One of 'lower_hall', 'upper_gallery', or 'vip'.
        city (str): City name (Birmingham, Bristol, Cardiff, London).

    Returns:
        float: Final ticket price rounded to 2 decimal places.

    Raises:
        ValueError: If ticket_type or city is not recognised.

    Example:
        >>> calculate_ticket_price(10.0, 'vip', 'London')
        14.4
    """
    # Example logic placeholder
    if ticket_type == 'vip':
        return round((base_price * 1.20) * 1.20, 2)
    return base_price
