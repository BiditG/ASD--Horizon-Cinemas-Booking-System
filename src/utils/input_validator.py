"""
src/utils/input_validator.py
============================
Utility class for sanitising and validating form inputs.
"""

import re
from datetime import datetime

class InputValidator:
    """Provides static methods for input sanitisation and validation."""

    @staticmethod
    def sanitise_text(value: str, max_length: int) -> str:
        """
        Strip leading/trailing whitespace, remove control characters,
        and truncate to max_length.
        """
        if not value:
            return ""
        # Remove control characters (characters with code point < 32)
        sanitised = "".join(ch for ch in value if ord(ch) >= 32)
        sanitised = sanitised.strip()
        return sanitised[:max_length]

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Regex check for valid email format.
        """
        if not email:
            return False
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return bool(re.match(pattern, email.strip()))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Accepts UK-format phone numbers.
        Allows optional leading +, spaces, and dashes.
        """
        if not phone:
            return False
        # Basic regex for UK phone formats: e.g. +44 7911 123456 or 07911 123456
        pattern = r"^(?:(?:\+44\s?|0)7\d{3}\s?\d{6}|(?:(?:\+44\s?|0)[1-35-9]\d{2,4}\s?\d{4,6}))$"
        sanitised_phone = phone.replace("-", "").replace("(", "").replace(")", "").strip()
        return bool(re.match(pattern, sanitised_phone))

    @staticmethod
    def validate_date(date_str: str, fmt: str = '%Y-%m-%d') -> bool:
        """
        Check if date string matches the expected format.
        """
        if not date_str:
            return False
        try:
            datetime.strptime(date_str.strip(), fmt)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_card_number(card: str) -> bool:
        """
        Validate a 16-digit card number using the Luhn algorithm.
        """
        if not card:
            return False
            
        card = card.replace(" ", "").replace("-", "").strip()
        if not card.isdigit() or len(card) != 16:
            return False
            
        total = 0
        reverse_digits = card[::-1]
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0
