"""Ride management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import User
from api.dependencies import get_current_user
from api.schemas import (
    RideCreate,
    RideUpdate,
    RideResponse,
    RideSearchRequest,
    RideNLPCreate,
)
from services.ride_service import RideService
from services.maps_service import MapsService
from utils.exceptions import (
    InvalidLocationException,
    InvalidTimeException,
    RideNotFoundException,
)
import logging

router = APIRouter(prefix="/api/rides", tags=["Rides"])
logger = logging.getLogger(__name__)
ride_service = RideService()
maps_service = MapsService()


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_ride(
    request: RideCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new ride posting."""
    try:
        ride = await ride_service.create_ride(
            db,
            user_id=current_user.id,
            source_address=request.source_address,
            destination_address=request.destination_address,
            departure_datetime=request.departure_datetime,
            seats_available=request.seats_available,
            vehicle_type=request.vehicle_type,
            vehicle_name=request.vehicle_name,
            vehicle_plate=request.vehicle_plate,
            ride_details=request.ride_details.dict()
        )
        
        return {
            "success": True,
            "data": {
                "id": ride.id,
                "user_id": ride.user_id,
                "source_address": ride.source_address,
                "destination_address": ride.destination_address,
                "departure_datetime": ride.departure_datetime,
                "seats_available": ride.seats_available,
                "vehicle_type": ride.vehicle_type,
                "status": ride.status,
                "created_at": ride.created_at,
            }
        }
    except InvalidLocationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidTimeException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Create ride error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create ride")


@router.get("/{ride_id}", response_model=dict)
async def get_ride(ride_id: int, db: Session = Depends(get_db)):
    """Get ride details by ID."""
    try:
        ride = RideService.get_ride_by_id(db, ride_id)
        
        ride_detail_data = None
        if ride.ride_details:
            ride_detail_data = {
                "id": ride.ride_details.id,
                "ride_id": ride.ride_details.ride_id,
                "smoking": ride.ride_details.smoking,
                "gender": ride.ride_details.gender,
                "music": ride.ride_details.music,
                "luggage": ride.ride_details.luggage,
                "ac_preference": ride.ride_details.ac_preference,
                "price_per_seat": ride.ride_details.price_per_seat,
                "notes": ride.ride_details.notes,
            }
        
        return {
            "success": True,
            "data": {
                "id": ride.id,
                "user_id": ride.user_id,
                "source_address": ride.source_address,
                "destination_address": ride.destination_address,
                "source_lat": ride.source_lat,
                "source_lng": ride.source_lng,
                "destination_lat": ride.destination_lat,
                "destination_lng": ride.destination_lng,
                "departure_datetime": ride.departure_datetime,
                "seats_available": ride.seats_available,
                "vehicle_type": ride.vehicle_type,
                "vehicle_name": ride.vehicle_name,
                "vehicle_plate": ride.vehicle_plate,
                "polyline": ride.polyline,
                "route_distance_km": ride.route_distance_km,
                "route_duration_minutes": ride.route_duration_minutes,
                "status": ride.status,
                "created_at": ride.created_at,
                "ride_details": ride_detail_data,
            }
        }
    except RideNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Get ride error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch ride")


@router.get("/my-rides", response_model=dict)
async def get_my_rides(
    status_filter: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's rides."""
    try:
        rides = RideService.get_user_rides(db, current_user.id, status=status_filter)
        
        rides_data = []
        for ride in rides:
            rides_data.append({
                "id": ride.id,
                "user_id": ride.user_id,
                "source_address": ride.source_address,
                "destination_address": ride.destination_address,
                "departure_datetime": ride.departure_datetime,
                "seats_available": ride.seats_available,
                "vehicle_type": ride.vehicle_type,
                "status": ride.status,
                "created_at": ride.created_at,
            })
        
        return {
            "success": True,
            "data": {
                "rides": rides_data,
                "count": len(rides_data)
            }
        }
    except Exception as e:
        logger.error(f"Get my rides error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch rides")


@router.post("/search", response_model=dict)
async def search_rides(
    request: RideSearchRequest,
    db: Session = Depends(get_db)
):
    """Search for rides with overlapping routes."""
    try:
        rides = RideService.search_rides(
            db,
            source_lat=request.source_lat,
            source_lng=request.source_lng,
            dest_lat=request.destination_lat,
            dest_lng=request.destination_lng,
            departure_date=request.departure_date,
            time_window_minutes=request.time_window_minutes
        )
        
        rides_data = []
        for ride in rides:
            rides_data.append({
                "id": ride.id,
                "user_id": ride.user_id,
                "source_address": ride.source_address,
                "destination_address": ride.destination_address,
                "departure_datetime": ride.departure_datetime,
                "seats_available": ride.seats_available,
                "vehicle_type": ride.vehicle_type,
                "route_distance_km": ride.route_distance_km,
                "route_duration_minutes": ride.route_duration_minutes,
                "status": ride.status,
            })
        
        return {
            "success": True,
            "data": {
                "rides": rides_data,
                "count": len(rides_data)
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Search rides error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search rides")


@router.put("/{ride_id}", response_model=dict)
async def update_ride(
    ride_id: int,
    request: RideUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update ride details."""
    try:
        ride = RideService.update_ride(
            db,
            ride_id,
            current_user.id,
            seats_available=request.seats_available,
            ride_details=request.ride_details.dict() if request.ride_details else None
        )
        
        return {
            "success": True,
            "data": {
                "id": ride.id,
                "seats_available": ride.seats_available,
                "updated_at": ride.updated_at,
            }
        }
    except RideNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Update ride error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update ride")


@router.delete("/{ride_id}", response_model=dict)
async def cancel_ride(
    ride_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a ride posting."""
    try:
        ride = RideService.cancel_ride(db, ride_id, current_user.id)
        
        return {
            "success": True,
            "data": {
                "id": ride.id,
                "status": ride.status,
            }
        }
    except RideNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Cancel ride error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel ride")


@router.post("/{ride_id}/complete", response_model=dict)
async def complete_ride(
    ride_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark ride as completed."""
    try:
        ride = RideService.complete_ride(db, ride_id, current_user.id)
        
        return {
            "success": True,
            "data": {
                "id": ride.id,
                "status": ride.status,
                "completed_at": ride.completed_at,
            }
        }
    except RideNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Complete ride error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete ride")
