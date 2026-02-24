# restaurant_management_component.py
"""
Restaurant Management Component: Deals with business logic surrounding restaurant management.
Interacts with: Restaurant Management API, Order Management Component, User Management Component, Database
Main Classes: Restaurant, MenuItem, Order
"""
from models import Restaurant, MenuItem, User, SimpleDatabase
from auth_component import AuthorizationComponent
from typing import Optional, List

class RestaurantManagementComponent:
    """
    Handles business logic for restaurants and menus.
    """

    def __init__(self, db: SimpleDatabase, auth_component: AuthorizationComponent):
        self.db = db
        self.auth_component = auth_component

    def create_restaurant(self, owner: User, name: str, location: str, contact_info: str, operating_hours: str) -> Optional[Restaurant]:
        """
        Allows a restaurant owner to create a new restaurant profile.
        """
        # Check if the user is actually a restaurant owner
        if owner.role != UserRole.RESTAURANT_OWNER:
            print("Error: Only restaurant owners can create a restaurant.")
            return None

        new_id = self.db.get_next_id('restaurant')
        new_restaurant = Restaurant(new_id, owner.user_id, name, location, contact_info, operating_hours)
        self.db.restaurants[new_id] = new_restaurant
        print(f"Restaurant '{name}' created successfully by owner {owner.name}.")
        return new_restaurant

    def update_restaurant_profile(self, requesting_user: User, restaurant_id: int, **kwargs) -> bool:
        """
        Updates restaurant information (name, location, hours, etc.).
        This method uses the AuthorizationComponent to enforce Issue 2:
        'The system shall restrict customers or other restaurant owners from being able to edit a restaurant's profile.'
        """
        restaurant = self.db.restaurants.get(restaurant_id)
        if not restaurant:
            print("Error: Restaurant not found.")
            return False

        # --- Authorization Check (Issue 2) ---
        if not self.auth_component.can_edit_restaurant(requesting_user, restaurant.owner_id):
            print("Error: You do not have permission to edit this restaurant's profile.")
            return False

        # --- Business Logic ---
        allowed_keys = ['name', 'location', 'contact_info', 'operating_hours']
        updated = False
        for key, value in kwargs.items():
            if key in allowed_keys and hasattr(restaurant, key):
                setattr(restaurant, key, value)
                updated = True
                print(f"Updated {key} for restaurant {restaurant_id}.")

        if updated:
            # In a real system, this would be an explicit database update.
            # Since we're using an in-memory object, the change is already reflected.
            print(f"Restaurant {restaurant_id} profile updated successfully.")
            return True
        else:
            print("No valid fields were provided for update.")
            return False

    def add_menu_item(self, requesting_user: User, restaurant_id: int, name: str, description: str, price: float) -> Optional[MenuItem]:
        """
        Adds a new menu item to a restaurant.
        """
        restaurant = self.db.restaurants.get(restaurant_id)
        if not restaurant:
            print("Error: Restaurant not found.")
            return None

        # Authorization: Only the restaurant owner can add items
        if not self.auth_component.can_edit_restaurant(requesting_user, restaurant.owner_id):
            print("Error: You do not have permission to add items to this restaurant's menu.")
            return None

        new_id = self.db.get_next_id('menu')
        new_item = MenuItem(new_id, restaurant_id, name, description, price)
        self.db.menu_items[new_id] = new_item
        restaurant.add_menu_item(new_item)  # Add to restaurant's in-memory list
        print(f"Menu item '{name}' added to restaurant {restaurant.name}.")
        return new_item

    def get_restaurant_by_owner(self, owner_id: int) -> List[Restaurant]:
        """Helper to find restaurants owned by a specific user."""
        return [r for r in self.db.restaurants.values() if r.owner_id == owner_id]
