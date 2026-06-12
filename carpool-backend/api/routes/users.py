"""User management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import User
from api.dependencies import get_current_user
from api.schemas import (
    UserResponse,
    UserProfileResponse,
    UserUpdate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserTrustScoreResponse,
)
from services.user_service import UserService
from utils.exceptions import UserNotFoundException, ValidationException
import logging

router = APIRouter(prefix="/api/users", tags=["Users"])
logger = logging.getLogger(__name__)


@router.get("/{user_id}", response_model=dict)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user profile by ID."""
    try:
        user = UserService.get_user_by_id(db, user_id)
        preferences = UserService.get_user_preferences(db, user_id)
        trust_score = UserService.get_trust_score(db, user_id)
        
        return {
            "success": True,
            "data": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
                "institute_email": user.institute_email,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified,
                "created_at": user.created_at,
                "preferences": {
                    "id": preferences.id,
                    "user_id": preferences.user_id,
                    "smoking": preferences.smoking,
                    "gender": preferences.gender,
                    "music": preferences.music,
                    "luggage": preferences.luggage,
                    "ac_preference": preferences.ac_preference,
                    "notes": preferences.notes,
                },
                "trust_score": trust_score
            }
        }
    except UserNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch user")


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user's profile."""
    try:
        preferences = UserService.get_user_preferences(db, current_user.id)
        trust_score = UserService.get_trust_score(db, current_user.id)
        
        return {
            "success": True,
            "data": {
                "id": current_user.id,
                "email": current_user.email,
                "name": current_user.name,
                "phone": current_user.phone,
                "institute_email": current_user.institute_email,
                "bio": current_user.bio,
                "profile_picture_url": current_user.profile_picture_url,
                "email_verified": current_user.email_verified,
                "phone_verified": current_user.phone_verified,
                "created_at": current_user.created_at,
                "last_login": current_user.last_login,
                "preferences": {
                    "id": preferences.id,
                    "user_id": preferences.user_id,
                    "smoking": preferences.smoking,
                    "gender": preferences.gender,
                    "music": preferences.music,
                    "luggage": preferences.luggage,
                    "ac_preference": preferences.ac_preference,
                    "notes": preferences.notes,
                },
                "trust_score": trust_score
            }
        }
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch user profile")


@router.put("/me", response_model=dict)
async def update_current_user(
    request: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    try:
        user = UserService.update_user(
            db,
            current_user.id,
            name=request.name,
            phone=request.phone,
            bio=request.bio,
            profile_picture_url=request.profile_picture_url
        )
        
        return {
            "success": True,
            "data": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
                "bio": user.bio,
                "profile_picture_url": user.profile_picture_url
            }
        }
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user")


@router.get("/{user_id}/preferences", response_model=dict)
async def get_user_preferences(user_id: int, db: Session = Depends(get_db)):
    """Get user preferences."""
    try:
        UserService.get_user_by_id(db, user_id)
        prefs = UserService.get_user_preferences(db, user_id)
        
        return {
            "success": True,
            "data": {
                "id": prefs.id,
                "user_id": prefs.user_id,
                "smoking": prefs.smoking,
                "gender": prefs.gender,
                "music": prefs.music,
                "luggage": prefs.luggage,
                "ac_preference": prefs.ac_preference,
                "notes": prefs.notes,
            }
        }
    except UserNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Get preferences error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch preferences")


@router.put("/{user_id}/preferences", response_model=dict)
async def update_user_preferences(
    user_id: int,
    request: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences."""
    # Check ownership
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update other users' preferences")
    
    try:
        prefs = UserService.set_user_preferences(
            db,
            user_id,
            smoking=request.smoking,
            gender=request.gender,
            music=request.music,
            luggage=request.luggage,
            ac_preference=request.ac_preference,
            notes=request.notes
        )
        
        return {
            "success": True,
            "data": {
                "id": prefs.id,
                "user_id": prefs.user_id,
                "smoking": prefs.smoking,
                "gender": prefs.gender,
                "music": prefs.music,
                "luggage": prefs.luggage,
                "ac_preference": prefs.ac_preference,
                "notes": prefs.notes,
            }
        }
    except UserNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Update preferences error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update preferences")


@router.get("/{user_id}/trust-score", response_model=dict)
async def get_user_trust_score(user_id: int, db: Session = Depends(get_db)):
    """Get user trust score."""
    try:
        UserService.get_user_by_id(db, user_id)
        trust_score = UserService.get_trust_score(db, user_id)
        
        return {
            "success": True,
            "data": trust_score
        }
    except UserNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Get trust score error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch trust score")
