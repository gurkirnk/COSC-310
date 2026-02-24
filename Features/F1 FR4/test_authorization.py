"""Unit tests for Issue 2 - Role-based authorization (AuthorizationServices)."""

import pytest
from fastapi import HTTPException

from app.repositories.user_repo import UserRepo
from app.services.authorization_services import AuthorizationServices, ROLE_PERMISSIONS

# ---------------------------------------------------------------------------
# Sample user data
# ---------------------------------------------------------------------------

SAMPLE_USERS = [
    {
        "id": "user-1",
        "name": "Alex",
        "email": "alexsmith@gmail.com",
        "phone_number": "123-456-7890",
        "password": "password",
        "role": "customer",
    },
    {
        "id": "user-2",
        "name": "Mario",
        "email": "mario@restaurant.com",
        "phone_number": "555-000-1111",
        "password": "secret",
        "role": "restaurant_owner",
    },
    {
        "id": "user-3",
        "name": "Dave",
        "email": "dave@delivery.com",
        "phone_number": "777-888-9999",
        "password": "drivepass",
        "role": "delivery_driver",
    },
    {
        "id": "user-4",
        "name": "AdminSue",
        "email": "sue@admin.com",
        "phone_number": "111-222-3333",
        "password": "adminpass",
        "role": "admin",
    },
]


def _make_service(mocker):
    """Return an AuthorizationServices instance backed by a mocked UserRepo."""
    mock_repo = mocker.Mock(spec=UserRepo)
    mock_repo.load_all_users.return_value = SAMPLE_USERS
    return AuthorizationServices(mock_repo)


# ---------------------------------------------------------------------------
# Customer restriction tests (Issue 2 core requirement)
# ---------------------------------------------------------------------------


def test_customer_cannot_manage_restaurant(mocker):
    """Customers must not be allowed to manage a restaurant profile."""
    service = _make_service(mocker)

    with pytest.raises(HTTPException) as exc_info:
        service.authorize("user-1", "manage_own_restaurant")

    assert exc_info.value.status_code == 403


def test_customer_cannot_manage_menu(mocker):
    """Customers must not be allowed to manage menu items."""
    service = _make_service(mocker)

    with pytest.raises(HTTPException) as exc_info:
        service.authorize("user-1", "manage_own_menu")

    assert exc_info.value.status_code == 403


def test_customer_cannot_accept_order(mocker):
    """Customers must not be allowed to accept orders on behalf of a restaurant."""
    service = _make_service(mocker)

    with pytest.raises(HTTPException) as exc_info:
        service.authorize("user-1", "accept_order")

    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Restaurant owner restriction tests (Issue 2 core requirement)
# ---------------------------------------------------------------------------


def test_restaurant_owner_cannot_manage_users(mocker):
    """Restaurant owners must not be allowed to manage other users."""
    service = _make_service(mocker)

    with pytest.raises(HTTPException) as exc_info:
        service.authorize("user-2", "manage_users")

    assert exc_info.value.status_code == 403


def test_restaurant_owner_cannot_create_order(mocker):
    """Restaurant owners must not be allowed to place customer orders."""
    service = _make_service(mocker)

    with pytest.raises(HTTPException) as exc_info:
        service.authorize("user-2", "create_order")

    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Permitted action tests
# ---------------------------------------------------------------------------


def test_customer_can_create_order(mocker):
    """Customers are permitted to create orders."""
    service = _make_service(mocker)
    assert service.authorize("user-1", "create_order") is True


def test_customer_can_browse_restaurants(mocker):
    """Customers are permitted to browse restaurants."""
    service = _make_service(mocker)
    assert service.authorize("user-1", "browse_restaurants") is True


def test_restaurant_owner_can_manage_own_restaurant(mocker):
    """Restaurant owners are permitted to manage their own restaurant profile."""
    service = _make_service(mocker)
    assert service.authorize("user-2", "manage_own_restaurant") is True


def test_restaurant_owner_can_manage_own_menu(mocker):
    """Restaurant owners are permitted to manage their own menu."""
    service = _make_service(mocker)
    assert service.authorize("user-2", "manage_own_menu") is True


def test_delivery_driver_can_update_delivery_status(mocker):
    """Delivery drivers are permitted to update delivery status."""
    service = _make_service(mocker)
    assert service.authorize("user-3", "update_delivery_status") is True


def test_admin_can_view_all_orders(mocker):
    """Admins are permitted to view all orders."""
    service = _make_service(mocker)
    assert service.authorize("user-4", "view_all_orders") is True


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


def test_authorize_unknown_user_raises_404(mocker):
    """Authorizing an unknown user raises 404."""
    service = _make_service(mocker)

    with pytest.raises(HTTPException) as exc_info:
        service.authorize("ghost-id", "create_order")

    assert exc_info.value.status_code == 404


def test_get_role_permissions_customer(mocker):
    """get_role_permissions returns expected actions for customer role."""
    service = _make_service(mocker)
    perms = service.get_role_permissions("customer")

    assert "create_order" in perms
    assert "manage_own_restaurant" not in perms


def test_get_role_permissions_restaurant_owner(mocker):
    """get_role_permissions returns expected actions for restaurant_owner role."""
    service = _make_service(mocker)
    perms = service.get_role_permissions("restaurant_owner")

    assert "manage_own_restaurant" in perms
    assert "create_order" not in perms


def test_get_role_permissions_unknown_role_raises_400(mocker):
    """Unknown role raises HTTPException 400."""
    service = _make_service(mocker)

    with pytest.raises(HTTPException) as exc_info:
        service.get_role_permissions("supervillain")

    assert exc_info.value.status_code == 400


def test_role_permissions_map_has_all_roles():
    """ROLE_PERMISSIONS contains all expected roles with non-empty permission lists."""
    for role in ("customer", "restaurant_owner", "delivery_driver", "admin"):
        assert role in ROLE_PERMISSIONS
        assert len(ROLE_PERMISSIONS[role]) > 0
