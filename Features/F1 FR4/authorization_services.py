"""Service layer for Issue 2 - Role-based authorization business logic.

Restricts customers and other restaurant owners from editing a restaurant's
profile by enforcing a role permission mapping on every action attempt.
"""

from fastapi import HTTPException

from app.repositories.user_repo import UserRepo

# Maps each role to the actions it is permitted to perform.
ROLE_PERMISSIONS: dict = {
    "customer": [
        "browse_restaurants",
        "create_order",
        "view_own_orders",
        "make_payment",
        "track_order",
        "manage_own_account",
    ],
    "restaurant_owner": [
        "browse_restaurants",
        "manage_own_restaurant",
        "manage_own_menu",
        "view_incoming_orders",
        "accept_order",
        "reject_order",
        "update_order_status",
        "manage_own_account",
    ],
    "delivery_driver": [
        "browse_restaurants",
        "view_delivery_requests",
        "accept_delivery",
        "reject_delivery",
        "update_delivery_status",
        "manage_own_account",
    ],
    "admin": [
        "browse_restaurants",
        "view_all_orders",
        "generate_reports",
        "manage_own_account",
        "manage_users",
    ],
}


class AuthorizationServices:
    """Handles role-based authorization checks."""

    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    def authorize(self, user_id: str, action: str) -> bool:
        """Check whether a user is permitted to perform the given action.

        Loads the current user list from the repo, finds the user by ID,
        and verifies that their role includes the requested action.

        Args:
            user_id: The ID of the user attempting the action.
            action:  The action string to check against ROLE_PERMISSIONS.

        Returns:
            True if the user's role permits the action.

        Raises:
            HTTPException 404 if the user is not found.
            HTTPException 403 if the role does not permit the action.
        """
        users = self.user_repo.load_all_users()
        user = next((u for u in users if u["id"] == user_id), None)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail=f"User '{user_id}' not found.",
            )

        role = user.get("role", "")
        allowed_actions = ROLE_PERMISSIONS.get(role, [])

        if action not in allowed_actions:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Access denied. Role '{role}' is not permitted "
                    f"to perform action '{action}'."
                ),
            )

        return True

    def get_role_permissions(self, role: str) -> list:
        """Return the list of permitted actions for a given role.

        Args:
            role: The role string to look up.

        Returns:
            List of permitted action strings.

        Raises:
            HTTPException 400 for unknown roles.
        """
        if role not in ROLE_PERMISSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown role '{role}'.",
            )
        return ROLE_PERMISSIONS[role]
