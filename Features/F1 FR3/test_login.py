"""Unit tests for Issue 1 - Login authentication (LoginServices)."""

import pytest
from fastapi import HTTPException

from app.repositories.auth_repo import AuthRepo
from app.schemas.auth_schema import LoginRequest
from app.services.login_services import LoginServices

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
]


def _make_service(mocker):
    """Return a LoginServices instance backed by a mocked AuthRepo."""
    mock_repo = mocker.Mock(spec=AuthRepo)
    mock_repo.find_user_by_email.side_effect = lambda email: next(
        (u for u in SAMPLE_USERS if u["email"].lower() == email.lower()), None
    )
    mock_repo.find_user_by_phone.side_effect = lambda phone: next(
        (u for u in SAMPLE_USERS if u["phone_number"] == phone), None
    )
    return LoginServices(mock_repo)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_login_with_email_success(mocker):
    """User can log in using their email and correct password."""
    service = _make_service(mocker)
    payload = LoginRequest(identifier="alexsmith@gmail.com", password="password")
    result = service.login(payload)

    assert result.user_id == "user-1"
    assert result.name == "Alex"
    assert result.role == "customer"


def test_login_with_phone_success(mocker):
    """User can log in using their phone number and correct password."""
    service = _make_service(mocker)
    payload = LoginRequest(identifier="123-456-7890", password="password")
    result = service.login(payload)

    assert result.user_id == "user-1"
    assert result.role == "customer"


def test_login_restaurant_owner_with_email(mocker):
    """Restaurant owner can log in using their email."""
    service = _make_service(mocker)
    payload = LoginRequest(identifier="mario@restaurant.com", password="secret")
    result = service.login(payload)

    assert result.user_id == "user-2"
    assert result.role == "restaurant_owner"


def test_login_restaurant_owner_with_phone(mocker):
    """Restaurant owner can log in using their phone number."""
    service = _make_service(mocker)
    payload = LoginRequest(identifier="555-000-1111", password="secret")
    result = service.login(payload)

    assert result.user_id == "user-2"
    assert result.role == "restaurant_owner"


def test_login_wrong_password_raises_401(mocker):
    """Wrong password results in a 401 HTTPException."""
    service = _make_service(mocker)
    payload = LoginRequest(identifier="alexsmith@gmail.com", password="wrongpass")

    with pytest.raises(HTTPException) as exc_info:
        service.login(payload)

    assert exc_info.value.status_code == 401
    assert "Incorrect password" in exc_info.value.detail


def test_login_unknown_email_raises_401(mocker):
    """Unregistered email results in a 401 HTTPException."""
    service = _make_service(mocker)
    payload = LoginRequest(identifier="ghost@example.com", password="password")

    with pytest.raises(HTTPException) as exc_info:
        service.login(payload)

    assert exc_info.value.status_code == 401
    assert "User not found" in exc_info.value.detail


def test_login_unknown_phone_raises_401(mocker):
    """Unregistered phone number results in a 401 HTTPException."""
    service = _make_service(mocker)
    payload = LoginRequest(identifier="000-000-0000", password="password")

    with pytest.raises(HTTPException) as exc_info:
        service.login(payload)

    assert exc_info.value.status_code == 401


def test_login_response_contains_welcome_message(mocker):
    """Successful login response contains a welcome message."""
    service = _make_service(mocker)
    payload = LoginRequest(identifier="alexsmith@gmail.com", password="password")
    result = service.login(payload)

    assert "Alex" in result.message
