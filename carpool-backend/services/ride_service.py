"""Ride management service."""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from database.models import Ride, RideDetails, User
from services.maps_service import MapsService
from services.user_service import UserService
from utils.exceptions import InvalidLocationException, InvalidTimeException, RideNotFoundException
from utils.validators import validate_coordinates, validate_datetime_future, validate_seats
import logging

logger = logging.getLogger(__name__)


class RideService:
    """Service for ride-related operations."""
    
    def __init__(self):
        self.maps_service = MapsService()

    async def create_ride(self, db: Session, user_id: int, source_address: str, 
                         destination_address: str, departure_datetime: datetime,
                         seats_available: int, vehicle_type: str, vehicle_name: Optional[str],
                         vehicle_plate: Optional[str], ride_details: Dict) -> Ride:
        """Create a new ride posting."""
        
        # Validate inputs
        if not validate_seats(seats_available):
            raise ValueError("Seats must be between 1 and 8")
        
        if not validate_datetime_future(departure_datetime):
            raise InvalidTimeException("Ride time must be at least 30 minutes in the future")
        
        # Geocode source and destination
        logger.info(f"Geocoding source: {source_address}")
        source_coords = await self.maps_service.geocode_address(source_address)
        
        logger.info(f"Geocoding destination: {destination_address}")
        dest_coords = await self.maps_service.geocode_address(destination_address)
        
        # Validate coordinates
        if not validate_coordinates(source_coords["lat"], source_coords["lng"]):
            raise InvalidLocationException("Invalid source coordinates")
        if not validate_coordinates(dest_coords["lat"], dest_coords["lng"]):
            raise InvalidLocationException("Invalid destination coordinates")
        
        # Check source != destination
        if (source_coords["lat"] == dest_coords["lat"] and 
            source_coords["lng"] == dest_coords["lng"]):
            raise ValueError("Source and destination cannot be the same")
        
        # Get route from OSRM
        logger.info(f"Getting route from OSRM")
        route_data = await self.maps_service.get_route(
            source_coords["lat"], source_coords["lng"],
            dest_coords["lat"], dest_coords["lng"]
        )
        
        # Create ride in database
        ride = Ride(
            user_id=user_id,
            source_lat=source_coords["lat"],
            source_lng=source_coords["lng"],
            destination_lat=dest_coords["lat"],
            destination_lng=dest_coords["lng"],
            source_address=source_coords.get("display_name", source_address),
            destination_address=dest_coords.get("display_name", destination_address),
            departure_datetime=departure_datetime,
            seats_available=seats_available,
            vehicle_type=vehicle_type,
            vehicle_name=vehicle_name,
            vehicle_plate=vehicle_plate,
            polyline=route_data.get("polyline"),
            route_distance_km=route_data.get("distance_km"),
            route_duration_minutes=route_data.get("duration_minutes"),
            status="active"
        )
        
        db.add(ride)
        db.flush()  # Get ride ID without committing
        
        # Create ride details
        ride_detail = RideDetails(
            ride_id=ride.id,
            smoking=ride_details.get("smoking", "no_preference"),
            gender=ride_details.get("gender", "any"),
            music=ride_details.get("music", "no_preference"),
            luggage=ride_details.get("luggage", "no_preference"),
            ac_preference=ride_details.get("ac_preference", "no_preference"),
            price_per_seat=ride_details.get("price_per_seat"),
            notes=ride_details.get("notes")
        )
        
        db.add(ride_detail)
        db.commit()
        db.refresh(ride)
        
        logger.info(f"Created ride {ride.id} for user {user_id}")
        
        return ride

    @staticmethod
    def get_ride_by_id(db: Session, ride_id: int) -> Ride:
        """Get ride by ID."""
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if not ride:
            raise RideNotFoundException(f"Ride {ride_id} not found")
        return ride

    @staticmethod
    def get_user_rides(db: Session, user_id: int, status: Optional[str] = None) -> List[Ride]:
        """Get rides posted by user."""
        query = db.query(Ride).filter(Ride.user_id == user_id)
        
        if status:
            query = query.filter(Ride.status == status)
        
        return query.order_by(Ride.departure_datetime.desc()).all()

    @staticmethod
    def search_rides(db: Session, source_lat: float, source_lng: float,
                    dest_lat: float, dest_lng: float, 
                    departure_date: str, time_window_minutes: int = 60) -> List[Ride]:
        """Search for rides with overlapping routes and times."""
        
        # Parse departure date and create time window
        try:
            date_obj = datetime.strptime(departure_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        
        window_start = date_obj
        window_end = date_obj + timedelta(days=1)
        
        # For now, return all active rides on that date
        # TODO: Implement proper spatial query with PostGIS
        rides = db.query(Ride).filter(
            and_(
                Ride.status == "active",
                Ride.departure_datetime >= window_start,
                Ride.departure_datetime < window_end,
                Ride.seats_available > 0
            )
        ).all()
        
        return rides

    @staticmethod
    def update_ride(db: Session, ride_id: int, user_id: int, 
                   seats_available: Optional[int] = None,
                   ride_details: Optional[Dict] = None) -> Ride:
        """Update ride details (only if not yet matched)."""
        ride = RideService.get_ride_by_id(db, ride_id)
        
        # Check ownership
        if ride.user_id != user_id:
            raise ValueError("You can only update your own rides")
        
        # Check if ride has matches
        if ride.matches and any(m.status in ["accepted", "completed"] for m in ride.matches):
            raise ValueError("Cannot update ride with active matches")
        
        if seats_available is not None:
            if not validate_seats(seats_available):
                raise ValueError("Seats must be between 1 and 8")
            ride.seats_available = seats_available
        
        if ride_details:
            ride_detail = ride.ride_details
            if not ride_detail:
                ride_detail = RideDetails(ride_id=ride_id)
                db.add(ride_detail)
            
            if "smoking" in ride_details:
                ride_detail.smoking = ride_details["smoking"]
            if "gender" in ride_details:
                ride_detail.gender = ride_details["gender"]
            if "music" in ride_details:
                ride_detail.music = ride_details["music"]
            if "luggage" in ride_details:
                ride_detail.luggage = ride_details["luggage"]
            if "ac_preference" in ride_details:
                ride_detail.ac_preference = ride_details["ac_preference"]
            if "price_per_seat" in ride_details:
                ride_detail.price_per_seat = ride_details["price_per_seat"]
            if "notes" in ride_details:
                ride_detail.notes = ride_details["notes"]
        
        ride.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ride)
        
        return ride

    @staticmethod
    def cancel_ride(db: Session, ride_id: int, user_id: int, reason: Optional[str] = None) -> Ride:
        """Cancel a ride posting."""
        ride = RideService.get_ride_by_id(db, ride_id)
        
        # Check ownership
        if ride.user_id != user_id:
            raise ValueError("You can only cancel your own rides")
        
        # Check if already completed
        if ride.status == "completed":
            raise ValueError("Cannot cancel a completed ride")
        
        ride.status = "cancelled"
        ride.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(ride)
        
        logger.info(f"Cancelled ride {ride_id}")
        
        return ride

    @staticmethod
    def complete_ride(db: Session, ride_id: int, user_id: int) -> Ride:
        """Mark ride as completed."""
        ride = RideService.get_ride_by_id(db, ride_id)
        
        # Check ownership
        if ride.user_id != user_id:
            raise ValueError("You can only complete your own rides")
        
        ride.status = "completed"
        ride.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(ride)
        
        # Recalculate trust scores for driver and all passengers
        UserService.calculate_trust_score(db, user_id)
        
        logger.info(f"Completed ride {ride_id}")
        
        return ride
