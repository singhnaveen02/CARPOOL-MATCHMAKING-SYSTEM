"""Pydantic request/response schemas."""

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any


# ============== Auth Schemas ==============
class SignupRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    phone: Optional[str] = None
    institute_email: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyEmailRequest(BaseModel):
    token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ============== User Schemas ==============
class UserPreferencesBase(BaseModel):
    smoking: str = "no_preference"
    gender: str = "any"
    music: str = "no_preference"
    luggage: str = "no_preference"
    ac_preference: str = "no_preference"
    notes: Optional[str] = None


class UserPreferencesCreate(UserPreferencesBase):
    pass


class UserPreferencesUpdate(UserPreferencesBase):
    pass


class UserPreferencesResponse(UserPreferencesBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class UserTrustScoreResponse(BaseModel):
    trust_score: float
    average_rating: float
    total_rides_completed: int
    total_rides_as_driver: int
    total_rides_as_passenger: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    institute_email: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None


class UserResponse(UserBase):
    id: int
    email_verified: bool
    phone_verified: bool
    created_at: datetime
    preferences: Optional[UserPreferencesResponse] = None
    trust_score: Optional[UserTrustScoreResponse] = None

    class Config:
        from_attributes = True


class UserProfileResponse(UserResponse):
    bio: Optional[str]
    last_login: Optional[datetime]


# ============== Ride Schemas ==============
class RideDetailsBase(BaseModel):
    smoking: str = "no_preference"
    gender: str = "any"
    music: str = "no_preference"
    luggage: str = "no_preference"
    ac_preference: str = "no_preference"
    price_per_seat: Optional[float] = None
    notes: Optional[str] = None


class RideDetailsCreate(RideDetailsBase):
    pass


class RideDetailsResponse(RideDetailsBase):
    id: int
    ride_id: int

    class Config:
        from_attributes = True


class RideBase(BaseModel):
    source_address: str
    destination_address: str
    departure_datetime: datetime
    seats_available: int = 1
    vehicle_type: str = "car"
    vehicle_name: Optional[str] = None
    vehicle_plate: Optional[str] = None

    @validator('seats_available')
    def validate_seats(cls, v):
        if not 1 <= v <= 8:
            raise ValueError('Seats must be between 1 and 8')
        return v


class RideCreate(RideBase):
    ride_details: RideDetailsCreate


class RideUpdate(BaseModel):
    seats_available: Optional[int] = None
    ride_details: Optional[RideDetailsCreate] = None


class RideResponse(RideBase):
    id: int
    user_id: int
    source_lat: float
    source_lng: float
    destination_lat: float
    destination_lng: float
    polyline: Optional[str]
    route_distance_km: Optional[float]
    route_duration_minutes: Optional[int]
    status: str
    created_at: datetime
    ride_details: Optional[RideDetailsResponse] = None

    class Config:
        from_attributes = True


class RideSearchRequest(BaseModel):
    source_lat: float
    source_lng: float
    destination_lat: float
    destination_lng: float
    departure_date: str  # YYYY-MM-DD
    time_window_minutes: int = 60


class RideNLPCreate(BaseModel):
    text: str = Field(..., min_length=10, max_length=1000)


# ============== Match Schemas ==============
class MatchResponse(BaseModel):
    id: int
    driver_id: int
    rider_id: int
    ride_id: int
    match_score: float
    route_overlap_percent: Optional[float]
    time_compatibility: Optional[float]
    preference_compatibility: Optional[float]
    explanation: Optional[str]
    status: str
    created_at: datetime
    driver: Optional[UserResponse] = None
    ride: Optional[RideResponse] = None

    class Config:
        from_attributes = True


class MatchAcceptRequest(BaseModel):
    pass


class MatchRejectRequest(BaseModel):
    reason: Optional[str] = None


class MatchListResponse(BaseModel):
    matches: List[MatchResponse]
    total_count: int


# ============== Rating Schemas ==============
class RatingCreate(BaseModel):
    to_user_id: int
    ride_id: int
    score: int = Field(..., ge=1, le=5)
    punctuality_rating: Optional[int] = Field(None, ge=1, le=5)
    cleanliness_rating: Optional[int] = Field(None, ge=1, le=5)
    behavior_rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class RatingResponse(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    ride_id: int
    score: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Notification Schemas ==============
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: Optional[str]
    message: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Error Schemas ==============
class ErrorResponse(BaseModel):
    detail: str
    status_code: int


# ============== Pagination ==============
class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 10

    @validator('skip')
    def skip_valid(cls, v):
        if v < 0:
            raise ValueError('skip must be >= 0')
        return v

    @validator('limit')
    def limit_valid(cls, v):
        if not 1 <= v <= 100:
            raise ValueError('limit must be between 1 and 100')
        return v
