"""Integration tests for Issue 1 - Login endpoint (POST /auth/login)."""

import json

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.auth_repo import AuthRepo
from app.repositories.user_repo import UserRepo
from app.routers.login import create_auth_repo

client = TestClient(app)

INITIAL_USERS = [
    {
        "id": "test-user-1",
        "name": "Alex",
        "email": "alexsmith@gmail.com",
        "phone_number": "123-456-7890",
        "password": "password",
        "role": "customer",
    },
    {
        "id": "test-user-2",
        "name": "Mario",
        "email": "mario@restaurant.com",
        "phone_number": "555-000-1111",
        "password": "secret",
        "role": "restaurant_owner",
    },
]


def _override_repo(tmp_path):
    """Write test users to a temp file and override the auth repo dependency."""
    test_user_data_path = tmp_path / "users.json"
    with open(test_user_data_path, "w", encoding="utf-8") as f:
        json.dump(INITIAL_USERS, f, ensure_ascii=False, indent=2)

    def override():
        user_repo = UserRepo(test_user_data_path)
        return AuthRepo(user_repo)

    app.dependency_overrides[create_auth_repo] = override


def test_login_with_email_success_integration(tmp_path):
    """POST /auth/login succeeds with valid email and password."""
    _override_repo(tmp_path)
    payload = {"identifier": "alexsmith@gmail.com", "password": "password"}
    r = client.post("/auth/login", json=payload)

    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == "test-user-1"
    assert data["role"] == "customer"
    assert data["name"] == "Alex"


def test_login_with_phone_success_integration(tmp_path):
    """POST /auth/login succeeds with valid phone number and password."""
    _override_repo(tmp_path)
    payload = {"identifier": "123-456-7890", "password": "password"}
    r = client.post("/auth/login", json=payload)

    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == "test-user-1"


def test_login_wrong_password_integration(tmp_path):
    """POST /auth/login returns 401 when password is incorrect."""
    _override_repo(tmp_path)
    payload = {"identifier": "alexsmith@gmail.com", "password": "wrongpassword"}
    r = client.post("/auth/login", json=payload)

    assert r.status_code == 401


def test_login_unknown_email_integration(tmp_path):
    """POST /auth/login returns 401 when email is not registered."""
    _override_repo(tmp_path)
    payload = {"identifier": "ghost@example.com", "password": "password"}
    r = client.post("/auth/login", json=payload)

    assert r.status_code == 401


def test_login_unknown_phone_integration(tmp_path):
    """POST /auth/login returns 401 when phone is not registered."""
    _override_repo(tmp_path)
    payload = {"identifier": "000-000-0000", "password": "password"}
    r = client.post("/auth/login", json=payload)

    assert r.status_code == 401


def test_login_response_schema_integration(tmp_path):
    """POST /auth/login response contains all required fields."""
    _override_repo(tmp_path)
    payload = {"identifier": "alexsmith@gmail.com", "password": "password"}
    r = client.post("/auth/login", json=payload)
    data = r.json()

    assert "user_id" in data
    assert "name" in data
    assert "role" in data
    assert "message" in data
