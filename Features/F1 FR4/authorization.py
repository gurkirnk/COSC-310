"""Authorization API endpoints - Issue 2.

GET /auth/permissions/{role}         — list all permitted actions for a role.
GET /auth/authorize/{user_id}/{action} — check whether a user may perform an action.
"""

from pathlib import Path

from fastapi import APIRouter, Depends

from app.repositories.user_repo import UserRepo
from app.services.authorization_services import AuthorizationServices

authorization_router = APIRouter(prefix="/auth", tags=["auth"])

USER_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "users.json"


def create_user_repo() -> UserRepo:
    """Initialize UserRepo with the users JSON file path."""
    return UserRepo(USER_DATA_PATH)


@authorization_router.get("/permissions/{role}", status_code=200)
def get_permissions(
    role: str,
    user_repo: UserRepo = Depends(create_user_repo),
):
    """Return the list of permitted actions for the given role.

    Returns 400 for unknown roles.
    """
    auth_service = AuthorizationServices(user_repo)
    permissions = auth_service.get_role_permissions(role)
    return {"role": role, "permissions": permissions}


@authorization_router.get("/authorize/{user_id}/{action}", status_code=200)
def check_authorization(
    user_id: str,
    action: str,
    user_repo: UserRepo = Depends(create_user_repo),
):
    """Check whether a user is permitted to perform the given action.

    Returns 200 if authorized, 403 if not permitted, 404 if user not found.
    """
    auth_service = AuthorizationServices(user_repo)
    auth_service.authorize(user_id, action)
    return {"user_id": user_id, "action": action, "authorized": True}
