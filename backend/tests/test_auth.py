"""
Tests for authentication endpoints.
"""

import pytest


async def test_register_success(client, unique_email):
    response = await client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == unique_email
    assert data["user"]["currency"] == "USD"
    assert "hashed_password" not in data["user"]
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


async def test_register_duplicate_email(client, unique_email):
    payload = {
        "email": unique_email,
        "password": "testpass123",
        "full_name": "Test User",
    }

    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 400
    assert "already exists" in second.json()["detail"]


async def test_register_missing_fields(client):
    response = await client.post(
        "/auth/register",
        json={"email": "incomplete@example.com"},
    )

    assert response.status_code == 422


async def test_login_success(client, unique_email):
    await client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User",
        },
    )

    response = await client.post(
        "/auth/login",
        json={"email": unique_email, "password": "testpass123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client, unique_email):
    await client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User",
        },
    )

    response = await client.post(
        "/auth/login",
        json={"email": unique_email, "password": "wrongpassword"},
    )

    assert response.status_code == 401


async def test_login_nonexistent_user(client):
    response = await client.post(
        "/auth/login",
        json={"email": "doesnotexist@example.com", "password": "testpass123"},
    )

    assert response.status_code == 401


async def test_me_requires_auth(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_with_valid_token(client, unique_email):
    register_response = await client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User",
        },
    )
    access_token = register_response.json()["tokens"]["access_token"]

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == unique_email


async def test_me_with_invalid_token(client):
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )

    assert response.status_code == 401


async def test_logout_and_refresh_revoked(client, unique_email):
    register_response = await client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User",
        },
    )
    tokens = register_response.json()["tokens"]
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    logout_response = await client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_response.status_code == 200

    refresh_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401