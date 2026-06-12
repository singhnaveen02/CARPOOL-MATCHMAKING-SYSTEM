"""User management service."""

from datetime import datetime
from sqlalchemy.orm import Session
from database.models import User, UserPreferences, UserTrustScore
from utils.exceptions import UserNotFoundException, ValidationException
from utils.validators import validate_phone
from utils.constants import (
    TRUST_WEIGHT_RATING,
    TRUST_WEIGHT_EXPERIENCE,
    TRUST_WEIGHT_RELIABILITY,
    TRUST_WEIGHT_VERIFICATION,
)
from sqlalchemy import func


class UserService:
    """Service for user-related operations."""

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException(f"User {user_id} not found")
        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        """Get user by email."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise UserNotFoundException(f"User with email {email} not found")
        return user

    @staticmethod
    def update_user(db: Session, user_id: int, name: str = None, phone: str = None, 
                   bio: str = None, profile_picture_url: str = None) -> User:
        """Update user profile."""
        user = UserService.get_user_by_id(db, user_id)
        
        if name is not None:
            user.name = name
        if phone is not None:
            if not validate_phone(phone):
                raise ValidationException("Invalid phone number")
            user.phone = phone
        if bio is not None:
            user.bio = bio
        if profile_picture_url is not None:
            user.profile_picture_url = profile_picture_url
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user

    @staticmethod
    def set_user_preferences(db: Session, user_id: int, smoking: str = None, 
                            gender: str = None, music: str = None, 
                            luggage: str = None, ac_preference: str = None,
                            notes: str = None) -> UserPreferences:
        """Set or update user preferences."""
        user = UserService.get_user_by_id(db, user_id)
        
        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        
        if prefs is None:
            prefs = UserPreferences(user_id=user_id)
            db.add(prefs)
        
        if smoking is not None:
            prefs.smoking = smoking
        if gender is not None:
            prefs.gender = gender
        if music is not None:
            prefs.music = music
        if luggage is not None:
            prefs.luggage = luggage
        if ac_preference is not None:
            prefs.ac_preference = ac_preference
        if notes is not None:
            prefs.notes = notes
        
        prefs.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(prefs)
        
        return prefs

    @staticmethod
    def get_user_preferences(db: Session, user_id: int) -> UserPreferences:
        """Get user preferences."""
        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        
        if prefs is None:
            # Create default preferences
            prefs = UserPreferences(user_id=user_id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        
        return prefs

    @staticmethod
    def calculate_trust_score(db: Session, user_id: int) -> float:
        """Calculate user trust score based on multiple factors."""
        from database.models import Rating, Ride, Match
        
        user = UserService.get_user_by_id(db, user_id)
        
        # Get trust score record or create one
        trust_record = db.query(UserTrustScore).filter(UserTrustScore.user_id == user_id).first()
        if not trust_record:
            trust_record = UserTrustScore(user_id=user_id)
            db.add(trust_record)
        
        # Factor 1: Average rating (40% weight)
        avg_rating = db.query(func.avg(Rating.score)).filter(
            Rating.to_user_id == user_id
        ).scalar() or 0
        rating_score = min(float(avg_rating) * 20, 100)  # 5 stars = 100
        
        # Factor 2: Ride experience (20% weight)
        ride_count = db.query(func.count(Ride.id)).filter(
            Ride.user_id == user_id,
            Ride.status == "completed"
        ).scalar() or 0
        experience_score = min(ride_count * 2, 100)  # 50+ rides = 100
        
        # Factor 3: Reliability - cancellation rate (20% weight)
        total_rides = db.query(func.count(Ride.id)).filter(
            Ride.user_id == user_id
        ).scalar() or 0
        cancellations = db.query(func.count(Ride.id)).filter(
            Ride.user_id == user_id,
            Ride.status == "cancelled"
        ).scalar() or 0
        
        if total_rides == 0:
            cancellation_rate = 0
        else:
            cancellation_rate = cancellations / total_rides
        
        reliability_score = 100 * (1 - cancellation_rate)
        
        # Factor 4: Email verification (10% weight)
        verification_score = 100 if user.email_verified else 0
        
        # Calculate weighted score
        trust_score = (
            rating_score * TRUST_WEIGHT_RATING +
            experience_score * TRUST_WEIGHT_EXPERIENCE +
            reliability_score * TRUST_WEIGHT_RELIABILITY +
            verification_score * TRUST_WEIGHT_VERIFICATION
        )
        
        # Cap at 100, floor at 0
        trust_score = max(0, min(100, trust_score))
        
        # Update trust record
        trust_record.average_rating = float(avg_rating)
        trust_record.total_rides_completed = int(ride_count)
        trust_record.total_rides_as_driver = int(
            db.query(func.count(Ride.id)).filter(
                Ride.user_id == user_id,
                Ride.status == "completed"
            ).scalar() or 0
        )
        trust_record.cancellation_count = int(cancellations)
        trust_record.trust_score = trust_score
        trust_record.last_updated = datetime.utcnow()
        
        if user.email_verified and not trust_record.email_verified_at:
            trust_record.email_verified_at = datetime.utcnow()
        
        db.commit()
        
        return trust_score

    @staticmethod
    def get_trust_score(db: Session, user_id: int) -> dict:
        """Get user trust score details."""
        trust_record = db.query(UserTrustScore).filter(
            UserTrustScore.user_id == user_id
        ).first()
        
        if not trust_record:
            UserService.calculate_trust_score(db, user_id)
            trust_record = db.query(UserTrustScore).filter(
                UserTrustScore.user_id == user_id
            ).first()
        
        return {
            "trust_score": float(trust_record.trust_score),
            "average_rating": float(trust_record.average_rating),
            "total_rides_completed": trust_record.total_rides_completed,
            "total_rides_as_driver": trust_record.total_rides_as_driver,
            "total_rides_as_passenger": trust_record.total_rides_as_passenger,
            "cancellation_count": trust_record.cancellation_count,
        }
