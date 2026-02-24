# auth_component.py
"""
Authorization Component: Deals with authenticating and authorizing users.
Interacts with: User Management Component, Payment Management Component, Database
Main Classes: Auth, User, Payment
"""
from models import User, UserRole, SimpleDatabase
from typing import Optional

class AuthorizationComponent:
    """
    Handles authorization checks. Determines if a user has permission
    to perform a specific action on a resource.
    """

    def __init__(self, db: SimpleDatabase):
        self.db = db

    def check_permission(self, user: Optional[User], required_role: UserRole, resource_owner_id: Optional[int] = None) -> bool:
        """
        Generic permission checker.
        - If a resource_owner_id is provided, it checks if the user is the owner (for modification rights).
        - Otherwise, it checks if the user has the required role.
        """
        if not user:
            print("Authorization Failed: No user provided.")
            return False

        # Admins can do almost everything (based on Admin use case)
        if user.role == UserRole.ADMIN:
            return True

        # Check for resource ownership (e.g., editing your own restaurant)
        if resource_owner_id is not None:
            if user.user_id == resource_owner_id:
                return True
            else:
                print(f"Authorization Failed: User {user.user_id} does not own this resource (owner ID: {resource_owner_id}).")
                return False

        # If no specific owner, just check the role
        if user.role == required_role:
            return True
        else:
            print(f"Authorization Failed: User has role '{user.role.value}', required '{required_role.value}'.")
            return False

    def can_edit_restaurant(self, user: Optional[User], restaurant_owner_id: int) -> bool:
        """
        Specific check for editing a restaurant's profile.
        Only the owner (or an admin) can edit. This directly fulfills Issue 2.
        """
        return self.check_permission(user, UserRole.RESTAURANT_OWNER, resource_owner_id=restaurant_owner_id)

    def can_manage_orders_as_restaurant(self, user: Optional[User], restaurant_owner_id: int) -> bool:
        """Check if a user can manage orders for a specific restaurant."""
        return self.check_permission(user, UserRole.RESTAURANT_OWNER, resource_owner_id=restaurant_owner_id)

    def can_manage_delivery(self, user: Optional[User], assigned_driver_id: Optional[int]) -> bool:
        """Check if a driver can update a specific delivery."""
        if not user:
            return False
        if user.role == UserRole.ADMIN:
            return True
        if user.role == UserRole.DELIVERY_DRIVER and user.user_id == assigned_driver_id:
            return True
        print(f"Authorization Failed: Driver {user.user_id} not assigned to this delivery.")
        return False

    def can_view_all_orders(self, user: Optional[User]) -> bool:
        """Check if a user can view all orders (Admin only)."""
        return user is not None and user.role == UserRole.ADMIN
