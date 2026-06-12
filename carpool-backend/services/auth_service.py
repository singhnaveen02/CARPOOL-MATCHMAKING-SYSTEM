"""Authentication service for user registration and login."""

from datetime import datetime, timedelta
from typing import Optional
import secrets
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from config import settings
from database.models import User
from utils.exceptions import (
    InvalidCredentialsException,
    EmailAlreadyExistsException,
    UserNotFoundException,
    ValidationException,
)
from utils.validators import validate_email, validate_password
import re

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("type") != token_type:
            raise JWTError("Invalid token type")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise JWTError("Invalid token")
        
        return payload
    except JWTError as e:
        raise InvalidCredentialsException(f"Invalid token: {str(e)}")


def generate_verification_token() -> str:
    """Generate email verification token."""
    return secrets.token_urlsafe(32)


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def signup(db: Session, email: str, name: str, password: str, phone: Optional[str] = None, institute_email: Optional[str] = None) -> dict:
        """Register new user."""
        # Validate email format
        if not validate_email(email):
            raise ValidationException("Invalid email format")
        
        # Validate password strength
        validate_password(password)
        
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise EmailAlreadyExistsException(f"Email {email} already registered")
        
        # Create new user
        verification_token = generate_verification_token()
        hashed_password = hash_password(password)
        
        new_user = User(
            email=email,
            name=name,
            phone=phone,
            institute_email=institute_email,
            password_hash=hashed_password,
            verification_token=verification_token,
            email_verified=False,
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # TODO: Send verification email with token
        
        return {
            "user_id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "message": "Check your email for verification link"
        }

    @staticmethod
    def verify_email(db: Session, token: str) -> dict:
        """Verify user email with token."""
        user = db.query(User).filter(User.verification_token == token).first()
        
        if not user:
            raise UserNotFoundException("Invalid verification token")
        
        user.email_verified = True
        user.email_verified_at = datetime.utcnow()
        user.verification_token = None
        
        db.commit()
        
        return {
            "user_id": user.id,
            "email": user.email,
            "message": "Email verified successfully"
        }

    @staticmethod
    def login(db: Session, email: str, password: str) -> dict:
        """Authenticate user and return tokens."""
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise InvalidCredentialsException("Invalid email or password")
        
        # Verify password
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException("Invalid email or password")
        
        if not user.is_active:
            raise InvalidCredentialsException("User account is disabled")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return {
            "user_id": user.id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> dict:
        """Generate new access token from refresh token."""
        try:
            payload = verify_token(refresh_token, token_type="refresh")
            user_id = int(payload.get("sub"))
            
            # Verify user still exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundException("User not found")
            
            # Create new access token
            access_token = create_access_token({"sub": str(user_id)})
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
        except Exception as e:
            raise InvalidCredentialsException(f"Failed to refresh token: {str(e)}")
