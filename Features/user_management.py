# user_management_component.py
"""
User Management Component: Deals with business logic surrounding user management.
Interacts with: User Management API, Order Management Component, Restaurant Management Component,
                Authorization Component, Notification Component, Database
Main Classes: Order, User, Restaurant, Auth, Cart
"""
from models import User, UserRole, SimpleDatabase
from auth_component import AuthorizationComponent
from typing import Optional

class UserManagementComponent:
    """
    Handles user-related business logic: registration, login, profile updates.
    """

    def __init__(self, db: SimpleDatabase, auth_component: AuthorizationComponent):
        self.db = db
        self.auth_component = auth_component
        # In a real app, you'd never store plain text passwords. This is a simulation.
        # For demo purposes, we'll use a simple dict to map passwords to users.
        self._user_credentials = {}  # In-memory store for simulation

    def register_user(self, name: str, email: Optional[str], phone: Optional[str], password: str, role: UserRole, address: Optional[str] = None) -> Optional[User]:
        """
        Registers a new user. (Extends Register an Account)
        Includes Update Database.
        """
        # Basic validation (FR: must have email or phone)
        if not email and not phone:
            print("Registration Error: User must have either an email or a phone number.")
            return None

        # Check if user already exists (simplified check)
        for user in self.db.users.values():
            if (email and user.email == email) or (phone and user.phone == phone):
                print("Registration Error: User with this email or phone already exists.")
                return None

        new_id = self.db.get_next_id('user')
        # In real life, hash the password!
        password_hash = f"hashed_{password}"  # Simulation only

        new_user = User(new_id, name, email, phone, password_hash, role, address)
        self.db.users[new_id] = new_user  # Includes Update Database
        self._user_credentials[new_id] = password  # Store for login simulation

        print(f"User '{name}' registered successfully with role {role.value}.")
        return new_user

    def login(self, identifier: str, password: str) -> Optional[User]:
        """
        Handles user login.
        Corresponds to Feat1-FR3: The system shall allow users to log in using
        identifying information of an email or phone number combined with a password.
        Includes Authentication.
        """
        # Find user by email or phone
        found_user: Optional[User] = None
        for user in self.db.users.values():
            if user.email == identifier or user.phone == identifier:
                found_user = user
                break

        if not found_user:
            print("Login Failed: No user found with that email/phone.")
            return None

        # --- Authentication Step ---
        stored_password = self._user_credentials.get(found_user.user_id)
        # In a real system, you'd compare hashed passwords
        if stored_password == password:
            print(f"Login Successful! Welcome, {found_user.name}. Role: {found_user.role.value}")
            return found_user
        else:
            print("Login Failed: Incorrect password.")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieves a user by their ID."""
        return self.db.users.get(user_id)

    def update_user_profile(self, user: User, name: Optional[str] = None, address: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Allows a user to update their own profile.
        Includes Update Database.
        """
        if not user:
            return False

        if name:
            user.name = name
        if address:
            user.address = address
        if password:
            # In real life, hash it!
            user.password_hash = f"hashed_{password}"
            self._user_credentials[user.user_id] = password

        # The 'user' object is a reference to the one in self.db.users, so it's automatically "updated".
        print(f"Profile updated for user {user.user_id}.")
        return True
