"""Service layer for Issue 1 - Login authentication business logic.

Allows users to log in using an email or phone number combined with a password.
"""

from fastapi import HTTPException

from app.repositories.auth_repo import AuthRepo
from app.schemas.auth_schema import LoginRequest, TokenResponse


class LoginServices:
    """Handles user login authentication."""

    def __init__(self, auth_repo: AuthRepo):
        self.auth_repo = auth_repo

    def login(self, payload: LoginRequest) -> TokenResponse:
        """Authenticate a user by email or phone number and password.

        Determines whether the identifier is an email (contains '@') or a
        phone number and looks the user up accordingly.

        Args:
            payload: LoginRequest containing identifier and password.

        Returns:
            TokenResponse with user_id, name, role, and a welcome message.

        Raises:
            HTTPException 401 if the user is not found or password is wrong.
        """
        identifier = payload.identifier.strip()
        password = payload.password.strip()

        # Determine lookup strategy: contains '@' → email, otherwise phone.
        if "@" in identifier:
            user = self.auth_repo.find_user_by_email(identifier)
        else:
            user = self.auth_repo.find_user_by_phone(identifier)

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials. User not found.",
            )

        if user.get("password") != password:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials. Incorrect password.",
            )

        return TokenResponse(
            user_id=user["id"],
            name=user["name"],
            role=user["role"],
            message=f"Login successful. Welcome, {user['name']}!",
        )
