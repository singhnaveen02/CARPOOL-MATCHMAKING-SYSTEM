"""Constants and enumerations."""

# Ride statuses
RIDE_STATUS_ACTIVE = "active"
RIDE_STATUS_COMPLETED = "completed"
RIDE_STATUS_CANCELLED = "cancelled"

RIDE_STATUSES = [RIDE_STATUS_ACTIVE, RIDE_STATUS_COMPLETED, RIDE_STATUS_CANCELLED]

# Match statuses
MATCH_STATUS_PENDING = "pending"
MATCH_STATUS_ACCEPTED = "accepted"
MATCH_STATUS_REJECTED = "rejected"
MATCH_STATUS_COMPLETED = "completed"
MATCH_STATUS_CANCELLED = "cancelled"

MATCH_STATUSES = [
    MATCH_STATUS_PENDING,
    MATCH_STATUS_ACCEPTED,
    MATCH_STATUS_REJECTED,
    MATCH_STATUS_COMPLETED,
    MATCH_STATUS_CANCELLED,
]

# Preference options
SMOKING_PREFERENCES = ["yes", "no", "no_preference"]
GENDER_PREFERENCES = ["male", "female", "any"]
MUSIC_PREFERENCES = ["yes", "no", "quiet", "no_preference"]
LUGGAGE_PREFERENCES = ["small", "medium", "large", "no_preference"]
AC_PREFERENCES = ["yes", "no", "no_preference"]

# Vehicle types
VEHICLE_TYPES = ["car", "auto", "van", "bike"]

# Notification types
NOTIFICATION_MATCH_FOUND = "match_found"
NOTIFICATION_MATCH_ACCEPTED = "match_accepted"
NOTIFICATION_MATCH_REJECTED = "match_rejected"
NOTIFICATION_RIDE_COMPLETED = "ride_completed"
NOTIFICATION_RATING_RECEIVED = "rating_received"

# Trust score weights
TRUST_WEIGHT_RATING = 0.4
TRUST_WEIGHT_EXPERIENCE = 0.2
TRUST_WEIGHT_RELIABILITY = 0.2
TRUST_WEIGHT_VERIFICATION = 0.1

# Match score weights
MATCH_WEIGHT_ROUTE = 0.4
MATCH_WEIGHT_TIME = 0.3
MATCH_WEIGHT_PREFERENCES = 0.2
MATCH_WEIGHT_TRUST = 0.1

# Default values
DEFAULT_SEATS = 1
MAX_SEATS = 8
MIN_RIDE_TIME_AHEAD_MINUTES = 30
MATCH_CACHE_TTL_SECONDS = 300  # 5 minutes
