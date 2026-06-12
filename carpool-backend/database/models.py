from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey,
    Text, DECIMAL, JSON, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database.connection import Base


class User(Base):
    """User model for drivers and passengers."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    institute_email = Column(String(255), index=True)
    profile_picture_url = Column(Text)
    bio = Column(Text)
    verification_token = Column(String(255))
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime)
    phone_verified = Column(Boolean, default=False)
    phone_verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    trust_score = relationship("UserTrustScore", back_populates="user", uselist=False, cascade="all, delete-orphan")
    rides = relationship("Ride", back_populates="user", foreign_keys="Ride.user_id", cascade="all, delete-orphan")
    matches_as_driver = relationship("Match", back_populates="driver", foreign_keys="Match.driver_id", cascade="all, delete-orphan")
    matches_as_rider = relationship("Match", back_populates="rider", foreign_keys="Match.rider_id", cascade="all, delete-orphan")
    ratings_given = relationship("Rating", back_populates="from_user", foreign_keys="Rating.from_user_id", cascade="all, delete-orphan")
    ratings_received = relationship("Rating", back_populates="to_user", foreign_keys="Rating.to_user_id", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class UserPreferences(Base):
    """User preferences for rides."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    smoking = Column(String(50), default="no_preference")
    gender = Column(String(50), default="any")
    music = Column(String(50), default="no_preference")
    luggage = Column(String(50), default="no_preference")
    ac_preference = Column(String(50), default="no_preference")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences")


class UserTrustScore(Base):
    """User trust score tracking."""
    __tablename__ = "user_trust_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    average_rating = Column(DECIMAL(3, 2), default=0)
    total_rides_completed = Column(Integer, default=0)
    total_rides_as_driver = Column(Integer, default=0)
    total_rides_as_passenger = Column(Integer, default=0)
    cancellation_count = Column(Integer, default=0)
    email_verified_at = Column(DateTime)
    phone_verified_at = Column(DateTime)
    trust_score = Column(DECIMAL(5, 2), default=0, index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="trust_score")


class Ride(Base):
    """Ride postings (Driver's rides)."""
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    source_lat = Column(Float, nullable=False)
    source_lng = Column(Float, nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lng = Column(Float, nullable=False)
    source_address = Column(String(500))
    destination_address = Column(String(500))
    departure_datetime = Column(DateTime, index=True, nullable=False)
    seats_available = Column(Integer, default=1, nullable=False)
    vehicle_type = Column(String(50))
    vehicle_name = Column(String(255))
    vehicle_plate = Column(String(50))
    polyline = Column(Text)  # Encoded polyline
    route_distance_km = Column(DECIMAL(10, 2))
    route_duration_minutes = Column(Integer)
    status = Column(String(50), index=True, default="active")
    is_recurring_series = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="rides", foreign_keys=[user_id])
    ride_details = relationship("RideDetails", back_populates="ride", uselist=False, cascade="all, delete-orphan")
    ride_occurrences = relationship("RideOccurrence", back_populates="ride", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="ride", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="ride", cascade="all, delete-orphan")


class RideDetails(Base):
    """Additional details and preferences for rides."""
    __tablename__ = "ride_details"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id", ondelete="CASCADE"), unique=True, nullable=False)
    smoking = Column(String(50), default="no_preference")
    gender = Column(String(50), default="any")
    music = Column(String(50), default="no_preference")
    luggage = Column(String(50), default="no_preference")
    ac_preference = Column(String(50), default="no_preference")
    price_per_seat = Column(DECIMAL(10, 2))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ride = relationship("Ride", back_populates="ride_details")


class RideOccurrence(Base):
    """Track individual occurrences of recurring rides."""
    __tablename__ = "ride_occurrences"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id", ondelete="CASCADE"), index=True, nullable=False)
    occurrence_date = Column(String(10), index=True, nullable=False)  # YYYY-MM-DD
    is_cancelled = Column(Boolean, default=False)
    cancellation_reason = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ride = relationship("Ride", back_populates="ride_occurrences")


class Match(Base):
    """Match between driver and passenger."""
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    rider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    ride_id = Column(Integer, ForeignKey("rides.id", ondelete="CASCADE"), index=True, nullable=False)
    match_score = Column(DECIMAL(5, 2), default=0)
    route_overlap_percent = Column(DECIMAL(5, 2))
    time_compatibility = Column(DECIMAL(5, 2))
    preference_compatibility = Column(DECIMAL(5, 2))
    explanation = Column(Text)
    status = Column(String(50), index=True, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime)
    completed_at = Column(DateTime)
    rating_from_driver_id = Column(Integer, ForeignKey("users.id"))
    rating_from_rider_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    driver = relationship("User", back_populates="matches_as_driver", foreign_keys=[driver_id])
    rider = relationship("User", back_populates="matches_as_rider", foreign_keys=[rider_id])
    ride = relationship("Ride", back_populates="matches")


class Rating(Base):
    """Ratings given by users for completed rides."""
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    ride_id = Column(Integer, ForeignKey("rides.id", ondelete="CASCADE"), index=True, nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="SET NULL"))
    score = Column(Integer, nullable=False)
    punctuality_rating = Column(Integer)
    cleanliness_rating = Column(Integer)
    behavior_rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    from_user = relationship("User", back_populates="ratings_given", foreign_keys=[from_user_id])
    to_user = relationship("User", back_populates="ratings_received", foreign_keys=[to_user_id])
    ride = relationship("Ride", back_populates="ratings")


class Notification(Base):
    """User notifications."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255))
    message = Column(Text, nullable=False)
    data = Column(JSON)
    read = Column(Boolean, index=True, default=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    read_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="notifications")
