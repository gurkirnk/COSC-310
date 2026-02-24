"""Repository layer for authentication - looks up users for login."""

from typing import Any, Dict, List, Optional, Protocol


class IUserRepo(Protocol):
    """Minimal user repo interface needed by auth."""

    def load_all_users(self) -> List[Dict[str, Any]]:
        """Load all users."""


class AuthRepo:
    """Handles user look-ups required for authentication."""

    def __init__(self, user_repo: IUserRepo):
        self.user_repo = user_repo

    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Return user dict whose email matches, or None."""
        users = self.user_repo.load_all_users()
        for user in users:
            if user.get("email", "").lower() == email.lower():
                return user
        return None

    def find_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Return user dict whose phone_number matches, or None."""
        users = self.user_repo.load_all_users()
        for user in users:
            if user.get("phone_number", "") == phone_number:
                return user
        return None
