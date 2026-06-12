"""Ratings endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import User, Rating, Ride
from api.dependencies import get_current_user
from api.schemas import RatingCreate
from services.user_service import UserService
from datetime import datetime
import logging

router = APIRouter(prefix="/api/ratings", tags=["Ratings"])
logger = logging.getLogger(__name__)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_rating(
    request: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a rating for a user after a completed ride."""
    try:
        # Verify ride exists
        ride = db.query(Ride).filter(Ride.id == request.ride_id).first()
        if not ride:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
        
        # Verify target user exists
        target_user = db.query(User).filter(User.id == request.to_user_id).first()
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
        
        # Check if rating already exists for this ride
        existing = db.query(Rating).filter(
            Rating.from_user_id == current_user.id,
            Rating.to_user_id == request.to_user_id,
            Rating.ride_id == request.ride_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Rating already exists for this ride")
        
        # Create rating
        rating = Rating(
            from_user_id=current_user.id,
            to_user_id=request.to_user_id,
            ride_id=request.ride_id,
            score=request.score,
            punctuality_rating=request.punctuality_rating,
            cleanliness_rating=request.cleanliness_rating,
            behavior_rating=request.behavior_rating,
            comment=request.comment
        )
        
        db.add(rating)
        db.commit()
        db.refresh(rating)
        
        # Update target user's trust score
        UserService.calculate_trust_score(db, request.to_user_id)
        
        logger.info(f"Created rating from user {current_user.id} to user {request.to_user_id}")
        
        return {
            "success": True,
            "data": {
                "id": rating.id,
                "from_user_id": rating.from_user_id,
                "to_user_id": rating.to_user_id,
                "score": rating.score,
                "created_at": rating.created_at,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create rating error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create rating")


@router.get("/{user_id}/received", response_model=dict)
async def get_user_ratings(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get ratings received by a user."""
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        ratings = db.query(Rating).filter(Rating.to_user_id == user_id).all()
        
        ratings_data = []
        for rating in ratings:
            ratings_data.append({
                "id": rating.id,
                "from_user_id": rating.from_user_id,
                "score": rating.score,
                "punctuality_rating": rating.punctuality_rating,
                "cleanliness_rating": rating.cleanliness_rating,
                "behavior_rating": rating.behavior_rating,
                "comment": rating.comment,
                "created_at": rating.created_at,
            })
        
        return {
            "success": True,
            "data": {
                "ratings": ratings_data,
                "count": len(ratings_data)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user ratings error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch ratings")
