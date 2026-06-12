from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://carpool_user:carpool_password@localhost:5432/carpool_db"
    
    # JWT Configuration
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # API Keys
    GEMINI_API_KEY: str = ""
    OSRM_API_URL: str = "https://router.project-osrm.org"
    
    # Email Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SENDER_EMAIL: str = "noreply@carpool.app"
    
    # App Configuration
    APP_NAME: str = "Carpool Matchmaking System"
    DEBUG: bool = True
    ALLOWED_HOSTS: list = ["localhost", "127.0.0.1"]
    
    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Nominatim API
    NOMINATIM_API_URL: str = "https://nominatim.openstreetmap.org"
    NOMINATIM_USER_AGENT: str = "carpool-app"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
