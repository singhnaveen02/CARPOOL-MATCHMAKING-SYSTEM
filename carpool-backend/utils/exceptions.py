"""Custom exception classes."""


class CarpoolException(Exception):
    """Base exception for carpool app."""
    pass


class InvalidCredentialsException(CarpoolException):
    """Raised when login credentials are invalid."""
    pass


class EmailAlreadyExistsException(CarpoolException):
    """Raised when email is already registered."""
    pass


class UserNotFoundException(CarpoolException):
    """Raised when user not found."""
    pass


class RideNotFoundException(CarpoolException):
    """Raised when ride not found."""
    pass


class InvalidLocationException(CarpoolException):
    """Raised when location cannot be geocoded."""
    pass


class InvalidTimeException(CarpoolException):
    """Raised when ride time is invalid."""
    pass


class MatchNotFoundException(CarpoolException):
    """Raised when match not found."""
    pass


class UnauthorizedException(CarpoolException):
    """Raised when user is not authorized."""
    pass


class ValidationException(CarpoolException):
    """Raised when validation fails."""
    pass
