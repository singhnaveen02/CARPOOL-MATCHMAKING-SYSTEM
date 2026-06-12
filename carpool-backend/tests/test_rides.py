"""test_rides.py - Ride endpoint tests."""

import pytest


def test_create_ride_requires_auth(client, test_ride_data):
    """Test that ride creation requires authentication."""
    response = client.post("/api/rides", json=test_ride_data)
    assert response.status_code == 403  # Forbidden (no token)


def test_create_ride_success(client, test_user_data, test_ride_data):
    """Test successful ride creation."""
    # Signup
    client.post("/api/auth/signup", json=test_user_data)
    
    # Login
    login_resp = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_resp.json()["data"]["access_token"]
    
    # Create ride
    response = client.post(
        "/api/rides",
        json=test_ride_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json()["success"] == True


def test_search_rides(client):
    """Test ride search."""
    response = client.post(
        "/api/rides/search",
        json={
            "source_lat": 29.9,
            "source_lng": 77.9,
            "destination_lat": 29.9,
            "destination_lng": 78.2,
            "departure_date": "2024-06-15"
        }
    )
    assert response.status_code == 200
    assert "rides" in response.json()["data"]


def test_get_ride(client, test_user_data, test_ride_data):
    """Test fetching ride details."""
    # Setup
    client.post("/api/auth/signup", json=test_user_data)
    login_resp = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_resp.json()["data"]["access_token"]
    
    # Create ride
    create_resp = client.post(
        "/api/rides",
        json=test_ride_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    ride_id = create_resp.json()["data"]["id"]
    
    # Get ride
    response = client.get(f"/api/rides/{ride_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == ride_id


def test_cancel_ride(client, test_user_data, test_ride_data):
    """Test ride cancellation."""
    # Setup
    client.post("/api/auth/signup", json=test_user_data)
    login_resp = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_resp.json()["data"]["access_token"]
    
    # Create ride
    create_resp = client.post(
        "/api/rides",
        json=test_ride_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    ride_id = create_resp.json()["data"]["id"]
    
    # Cancel ride
    response = client.delete(
        f"/api/rides/{ride_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "cancelled"
