"""Recurring rides service."""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import Ride, RideOccurrence
import logging

logger = logging.getLogger(__name__)


class RecurringRideService:
    """Service for managing recurring ride patterns."""

    @staticmethod
    def create_recurring_ride(db: Session, ride_id: int, frequency: str,
                            days: List[str], end_date: Optional[str] = None) -> dict:
        """Create recurring pattern for a ride."""
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if not ride:
            raise ValueError("Ride not found")

        recurrence_pattern = {
            "frequency": frequency,  # daily, weekly, monthly
            "days": days,  # ["Mon", "Tue", ...]
            "end_date": end_date or (datetime.utcnow() + timedelta(days=90)).isoformat()
        }

        ride.is_recurring_series = True
        ride.recurrence_pattern = recurrence_pattern
        db.commit()

        # Generate occurrences
        occurrences = RecurringRideService._generate_occurrences(
            ride.departure_datetime, end_date, frequency, days
        )

        for occ_date in occurrences:
            occurrence = RideOccurrence(
                ride_id=ride_id,
                occurrence_date=occ_date.strftime("%Y-%m-%d"),
                is_cancelled=False
            )
            db.add(occurrence)

        db.commit()

        return {"message": f"Recurring ride created with {len(occurrences)} occurrences"}

    @staticmethod
    def _generate_occurrences(start_date: datetime, end_date: Optional[str],
                            frequency: str, days: List[str]) -> List[datetime]:
        """Generate occurrence dates for recurring ride."""
        occurrences = []
        current = start_date
        
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = current + timedelta(days=90)

        day_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

        while current <= end:
            if frequency == "daily":
                occurrences.append(current)
                current += timedelta(days=1)
            elif frequency == "weekly":
                if current.strftime("%a") in days:
                    occurrences.append(current)
                current += timedelta(days=1)

        return occurrences

    @staticmethod
    def cancel_occurrence(db: Session, occurrence_id: int, reason: str = None):
        """Cancel a single occurrence of recurring ride."""
        occurrence = db.query(RideOccurrence).filter(RideOccurrence.id == occurrence_id).first()
        if occurrence:
            occurrence.is_cancelled = True
            occurrence.cancellation_reason = reason
            db.commit()

    @staticmethod
    def get_active_occurrences(db: Session, ride_id: int) -> List[RideOccurrence]:
        """Get all active occurrences for a recurring ride."""
        return db.query(RideOccurrence).filter(
            RideOccurrence.ride_id == ride_id,
            RideOccurrence.is_cancelled == False
        ).all()
