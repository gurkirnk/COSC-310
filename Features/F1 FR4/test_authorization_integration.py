"""Integration tests for Issue 2 - Authorization endpoints."""

import json

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.user_repo import UserRepo
from app.routers.authorization import create_user_repo

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
    """Write test users to a temp file and override the user repo dependency."""
    test_user_data_path = tmp_path / "users.json"
    with open(test_user_data_path, "w", encoding="utf-8") as f:
        json.dump(INITIAL_USERS, f, ensure_ascii=False, indent=2)

    def override():
        return UserRepo(test_user_data_path)

    app.dependency_overrides[create_user_repo] = override


# ---------------------------------------------------------------------------
# /auth/authorize tests
# ---------------------------------------------------------------------------


def test_customer_cannot_manage_restaurant_integration(tmp_path):
    """GET /auth/authorize returns 403 when a customer tries to manage a restaurant."""
    _override_repo(tmp_path)
    r = client.get("/auth/authorize/test-user-1/manage_own_restaurant")

    assert r.status_code == 403


def test_customer_cannot_manage_menu_integration(tmp_path):
    """GET /auth/authorize returns 403 when a customer tries to manage a menu."""
    _override_repo(tmp_path)
    r = client.get("/auth/authorize/test-user-1/manage_own_menu")

    assert r.status_code == 403


def test_restaurant_owner_cannot_create_order_integration(tmp_path):
    """GET /auth/authorize returns 403 when a restaurant owner tries to create an order."""
    _override_repo(tmp_path)
    r = client.get("/auth/authorize/test-user-2/create_order")

    assert r.status_code == 403


def test_customer_can_create_order_integration(tmp_path):
    """GET /auth/authorize returns 200 when a customer creates an order."""
    _override_repo(tmp_path)
    r = client.get("/auth/authorize/test-user-1/create_order")

    assert r.status_code == 200
    assert r.json()["authorized"] is True


def test_restaurant_owner_can_manage_restaurant_integration(tmp_path):
    """GET /auth/authorize returns 200 when a restaurant owner manages their restaurant."""
    _override_repo(tmp_path)
    r = client.get("/auth/authorize/test-user-2/manage_own_restaurant")

    assert r.status_code == 200
    assert r.json()["authorized"] is True


def test_authorize_unknown_user_returns_404_integration(tmp_path):
    """GET /auth/authorize returns 404 for a non-existent user."""
    _override_repo(tmp_path)
    r = client.get("/auth/authorize/ghost-id/create_order")

    assert r.status_code == 404


# ---------------------------------------------------------------------------
# /auth/permissions tests
# ---------------------------------------------------------------------------


def test_get_customer_permissions_integration(tmp_path):
    """GET /auth/permissions/customer returns expected permissions."""
    _override_repo(tmp_path)
    r = client.get("/auth/permissions/customer")

    assert r.status_code == 200
    data = r.json()
    assert data["role"] == "customer"
    assert "create_order" in data["permissions"]
    assert "manage_own_restaurant" not in data["permissions"]


def test_get_restaurant_owner_permissions_integration(tmp_path):
    """GET /auth/permissions/restaurant_owner returns expected permissions."""
    _override_repo(tmp_path)
    r = client.get("/auth/permissions/restaurant_owner")

    assert r.status_code == 200
    data = r.json()
    assert "manage_own_restaurant" in data["permissions"]
    assert "create_order" not in data["permissions"]


def test_get_unknown_role_permissions_returns_400_integration(tmp_path):
    """GET /auth/permissions/{unknown} returns 400 for an unknown role."""
    _override_repo(tmp_path)
    r = client.get("/auth/permissions/supervillain")

    assert r.status_code == 400
