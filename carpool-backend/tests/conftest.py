"""conftest.py - Pytest configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base
from database.connection import get_db
from main import app
from fastapi.testclient import TestClient

# Test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Create fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """FastAPI test client with overridden dependencies."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data for signup."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "TestPass123",
        "phone": "9876543210"
    }


@pytest.fixture
def test_ride_data():
    """Test ride data for creation."""
    return {
        "source_address": "IIT Roorkee, Roorkee",
        "destination_address": "Haridwar, India",
        "departure_datetime": "2024-06-15T08:00:00",
        "seats_available": 3,
        "vehicle_type": "car",
        "ride_details": {
            "smoking": "no",
            "music": "quiet",
            "price_per_seat": 100
        }
    }
