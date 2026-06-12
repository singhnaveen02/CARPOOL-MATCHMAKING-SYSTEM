"""Matches and recommendations endpoints with ML-powered matching."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from database.connection import get_db
from database.models import User, Match
from api.dependencies import get_current_user
from api.schemas import RideSearchRequest
from services.match_service import MatchService
from services.ride_service import RideService
from services.user_service import UserService
from ml.feature_engineering import FeatureEngineering
import logging

router = APIRouter(prefix="/api/matches", tags=["Matches"])
logger = logging.getLogger(__name__)


@router.post("/find", response_model=dict)
async def find_matches_for_search(
    request: RideSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find matches for a user's search (rider perspective)."""
    try:
        from datetime import datetime as dt
        # Create a temporary ride for matching calculation
        search_date = dt.fromisoformat(request.departure_date + " 12:00:00")
        
        matches = MatchService.find_matches_for_ride(
            db,
            ride_id=0,
            user_id=current_user.id,
            source_lat=request.source_lat,
            source_lng=request.source_lng,
            dest_lat=request.destination_lat,
            dest_lng=request.destination_lng,
            departure_time=search_date,
            min_score=50.0
        )
        
        return {
            "success": True,
            "data": {
                "matches": matches,
                "count": len(matches)
            }
        }
    except Exception as e:
        logger.error(f"Find matches error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to find matches")


@router.get("/for-ride/{ride_id}", response_model=dict)
async def get_ride_matches(
    ride_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ML-ranked matches for a specific ride (driver perspective)."""
    try:
        # Verify ride ownership
        ride = RideService.get_ride_by_id(db, ride_id)
        if ride.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your ride")
        
        # Find matches for this ride
        matches = MatchService.find_matches_for_ride(
            db,
            ride_id=ride_id,
            user_id=current_user.id,
            source_lat=ride.source_lat,
            source_lng=ride.source_lng,
            dest_lat=ride.destination_lat,
            dest_lng=ride.destination_lng,
            departure_time=ride.departure_datetime,
            min_score=50.0
        )
        
        return {
            "success": True,
            "data": {
                "matches": matches,
                "count": len(matches)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get ride matches error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch matches")


@router.post("/{match_id}/accept", response_model=dict)
async def accept_match(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a match."""
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
        
        # Check if current user is the rider
        if match.rider_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only rider can accept match")
        
        match.status = "accepted"
        match.accepted_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "data": {
                "id": match.id,
                "status": match.status,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Accept match error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to accept match")


@router.post("/{match_id}/reject", response_model=dict)
async def reject_match(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a match."""
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
        
        # Check if current user is the rider
        if match.rider_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only rider can reject match")
        
        match.status = "rejected"
        db.commit()
        
        return {
            "success": True,
            "data": {
                "id": match.id,
                "status": match.status,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reject match error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reject match")
