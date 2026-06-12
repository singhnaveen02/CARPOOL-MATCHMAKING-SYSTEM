"""test_auth.py - Authentication endpoint tests."""

import pytest


def test_signup_success(client, test_user_data):
    """Test successful user signup."""
    response = client.post("/api/auth/signup", json=test_user_data)
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert response.json()["data"]["email"] == test_user_data["email"]


def test_signup_invalid_email(client):
    """Test signup with invalid email."""
    response = client.post("/api/auth/signup", json={
        "email": "invalid-email",
        "name": "Test",
        "password": "TestPass123"
    })
    assert response.status_code == 400


def test_signup_weak_password(client):
    """Test signup with weak password."""
    response = client.post("/api/auth/signup", json={
        "email": "test@example.com",
        "name": "Test",
        "password": "weak"
    })
    assert response.status_code == 400


def test_signup_duplicate_email(client, test_user_data):
    """Test signup with already registered email."""
    # First signup
    client.post("/api/auth/signup", json=test_user_data)
    
    # Second signup with same email
    response = client.post("/api/auth/signup", json=test_user_data)
    assert response.status_code == 409


def test_login_success(client, test_user_data):
    """Test successful login."""
    # First signup
    client.post("/api/auth/signup", json=test_user_data)
    
    # Then login
    response = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
    assert "refresh_token" in response.json()["data"]


def test_login_invalid_credentials(client, test_user_data):
    """Test login with wrong password."""
    # First signup
    client.post("/api/auth/signup", json=test_user_data)
    
    # Try login with wrong password
    response = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": "WrongPassword123"
    })
    assert response.status_code == 401


def test_login_user_not_found(client):
    """Test login with non-existent user."""
    response = client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "SomePass123"
    })
    assert response.status_code == 401
