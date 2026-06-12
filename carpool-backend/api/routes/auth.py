"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from api.schemas import (
    SignupRequest,
    LoginRequest,
    VerifyEmailRequest,
    TokenResponse,
    RefreshTokenRequest,
)
from services.auth_service import AuthService
from utils.exceptions import (
    InvalidCredentialsException,
    EmailAlreadyExistsException,
    ValidationException,
)
import logging

router = APIRouter(prefix="/api/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=dict)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        result = AuthService.signup(
            db,
            email=request.email,
            name=request.name,
            password=request.password,
            phone=request.phone,
            institute_email=request.institute_email
        )
        return {
            "success": True,
            "data": result
        }
    except EmailAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Signup failed")


@router.post("/verify-email", response_model=dict)
async def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify user email with token."""
    try:
        result = AuthService.verify_email(db, token=request.token)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")


@router.post("/login", response_model=dict)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return tokens."""
    try:
        result = AuthService.login(db, email=request.email, password=request.password)
        return {
            "success": True,
            "data": result
        }
    except InvalidCredentialsException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


@router.post("/refresh", response_model=dict)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Generate new access token from refresh token."""
    try:
        result = AuthService.refresh_access_token(db, refresh_token=request.refresh_token)
        return {
            "success": True,
            "data": result
        }
    except InvalidCredentialsException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed")


@router.post("/logout", response_model=dict)
async def logout():
    """Logout user (client should delete tokens)."""
    return {
        "success": True,
        "message": "Please delete tokens from client"
    }
