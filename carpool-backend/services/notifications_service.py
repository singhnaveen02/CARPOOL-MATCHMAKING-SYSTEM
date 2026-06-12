"""Notifications service for real-time updates."""

from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from database.models import Notification, User


class NotificationService:
    """Service for notifications management."""

    @staticmethod
    def create_notification(db: Session, user_id: int, notif_type: str, 
                           title: str, message: str, data: dict = None) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            type=notif_type,
            title=title,
            message=message,
            data=data or {},
            read=False,
            created_at=datetime.utcnow()
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return notification

    @staticmethod
    def get_user_notifications(db: Session, user_id: int, unread_only: bool = False) -> List[Notification]:
        """Get notifications for a user."""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.read == False)
        
        return query.order_by(Notification.created_at.desc()).all()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int) -> Notification:
        """Mark notification as read."""
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if notif:
            notif.read = True
            notif.read_at = datetime.utcnow()
            db.commit()
            db.refresh(notif)
        
        return notif

    @staticmethod
    def notify_match_found(db: Session, rider_id: int, driver_name: str, match_score: float):
        """Notify user of new match."""
        NotificationService.create_notification(
            db, rider_id,
            type="match_found",
            title=f"New Match: {driver_name}",
            message=f"Great match with {driver_name}! Compatibility: {match_score:.0f}%",
            data={"match_score": match_score, "driver_name": driver_name}
        )

    @staticmethod
    def notify_match_accepted(db: Session, user_id: int, other_name: str):
        """Notify match acceptance."""
        NotificationService.create_notification(
            db, user_id,
            type="match_accepted",
            title="Ride Confirmed!",
            message=f"{other_name} has confirmed the ride.",
            data={"user_name": other_name}
        )
