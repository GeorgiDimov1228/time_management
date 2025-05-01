import pytest


def test_login_success(client, test_admin):
    # Test successful login and token retrieval
    response = client.post(
        "/api/token",
        data={"username": "admin", "password": "adminpassword", "grant_type": "password"}
    )
    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response


def test_login_wrong_password(client, test_admin):
    # Test login with wrong password
    response = client.post(
        "/api/token",
        data={"username": "admin", "password": "wrongpassword", "grant_type": "password"}
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    # Test login with a user that doesn't exist
    response = client.post(
        "/api/token",
        data={"username": "nonexistent", "password": "irrelevant", "grant_type": "password"}
    )
    assert response.status_code == 401


def test_protected_route_without_token(client):
    # Test accessing a protected route without token
    response = client.get("/api/users")
    assert response.status_code == 401


def test_protected_route_with_token(client, test_admin):
    # Test accessing a protected route with a valid token
    login_response = client.post(
        "/api/token",
        data={"username": "admin", "password": "adminpassword", "grant_type": "password"}
    )
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    response = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200 