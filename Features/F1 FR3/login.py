"""Login API endpoint - Issue 1.

POST /auth/login  — authenticate with email or phone number plus password.
"""

from pathlib import Path

from fastapi import APIRouter, Depends

from app.repositories.auth_repo import AuthRepo
from app.repositories.user_repo import UserRepo
from app.schemas.auth_schema import LoginRequest, TokenResponse
from app.services.login_services import LoginServices

login_router = APIRouter(prefix="/auth", tags=["auth"])

USER_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "users.json"


def create_auth_repo() -> AuthRepo:
    """Initialize AuthRepo backed by the users JSON file."""
    user_repo = UserRepo(USER_DATA_PATH)
    return AuthRepo(user_repo)


@login_router.post("/login", response_model=TokenResponse, status_code=200)
def login(
    payload: LoginRequest,
    auth_repo: AuthRepo = Depends(create_auth_repo),
):
    """Authenticate a user using email or phone number plus password.

    Returns user_id, name, role, and a welcome message on success.
    Returns 401 on invalid credentials.
    """
    login_service = LoginServices(auth_repo)
    return login_service.login(payload)
