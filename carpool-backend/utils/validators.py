"""Input validation utilities."""

import re
from datetime import datetime
from utils.exceptions import ValidationException


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> bool:
    """Validate password strength (min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit)."""
    if len(password) < 8:
        raise ValidationException("Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        raise ValidationException("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        raise ValidationException("Password must contain at least one lowercase letter")
    if not re.search(r'\d', password):
        raise ValidationException("Password must contain at least one digit")
    return True


def validate_phone(phone: str) -> bool:
    """Validate phone number (10 digits for India)."""
    digits = re.sub(r'\D', '', phone)
    return len(digits) == 10


def validate_coordinates(lat: float, lng: float) -> bool:
    """Validate latitude and longitude."""
    return -90 <= lat <= 90 and -180 <= lng <= 180


def validate_datetime_future(dt: datetime, min_minutes_ahead: int = 30) -> bool:
    """Validate that datetime is in the future."""
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    min_time = now + timedelta(minutes=min_minutes_ahead)
    return dt > min_time


def validate_seats(seats: int) -> bool:
    """Validate number of seats."""
    return 1 <= seats <= 8


def validate_rating(score: int) -> bool:
    """Validate rating score."""
    return 1 <= score <= 5
