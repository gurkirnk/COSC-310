# models.py
"""
Model classes representing the core data structures of the system.
Corresponds to the 'Model' layer in the MVC architecture and the 'Main Classes' in the component identification.
"""

import enum
from datetime import datetime
from typing import Optional, List

# --- Enums for Status ---
class OrderStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FULFILLED = "fulfilled"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"

class UserRole(enum.Enum):
    CUSTOMER = "customer"
    RESTAURANT_OWNER = "restaurant_owner"
    DELIVERY_DRIVER = "delivery_driver"
    ADMIN = "admin"

class DeliveryStatus(enum.Enum):
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    REJECTED = "rejected"

# --- Model Classes ---
class User:
    """Represents a user in the system. (From Class Diagram & User Management Component)"""
    def __init__(self, user_id: int, name: str, email: Optional[str], phone: Optional[str], password_hash: str, role: UserRole, address: Optional[str] = None):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.password_hash = password_hash  # In a real system, this would be a hashed value
        self.role = role
        self.address = address

    def __repr__(self):
        return f"<User {self.name} ({self.role.value})>"


class Restaurant:
    """Represents a restaurant. (From Class Diagram & Restaurant Management Component)"""
    def __init__(self, restaurant_id: int, owner_id: int, name: str, location: str, contact_info: str, operating_hours: str):
        self.restaurant_id = restaurant_id
        self.owner_id = owner_id  # The user_id of the restaurant owner
        self.name = name
        self.location = location
        self.contact_info = contact_info
        self.operating_hours = operating_hours
        self.menu: List[MenuItem] = []  # A restaurant has a list of menu items

    def add_menu_item(self, item: 'MenuItem'):
        self.menu.append(item)

    def __repr__(self):
        return f"<Restaurant {self.name}>"


class MenuItem:
    """Represents an item on a restaurant's menu. (From Class Diagram)"""
    def __init__(self, item_id: int, restaurant_id: int, name: str, description: str, price: float, is_available: bool = True):
        self.item_id = item_id
        self.restaurant_id = restaurant_id
        self.name = name
        self.description = description
        self.price = price
        self.is_available = is_available

    def __repr__(self):
        return f"<MenuItem {self.name}: ${self.price}>"


class Order:
    """Represents a customer's order. (From Class Diagram & Order Management Component)"""
    def __init__(self, order_id: int, customer_id: int, restaurant_id: int, items: List[MenuItem], delivery_address: str):
        self.order_id = order_id
        self.customer_id = customer_id
        self.restaurant_id = restaurant_id
        self.items = items
        self.delivery_address = delivery_address
        self.order_status = OrderStatus.PENDING
        self.payment_status = PaymentStatus.PENDING
        self.created_at = datetime.now()
        self.assigned_driver_id: Optional[int] = None

    def update_status(self, new_status: OrderStatus):
        # Business logic: Cannot change fulfilled orders (from Feat4-FR5)
        if self.order_status == OrderStatus.FULFILLED:
            raise Exception("Cannot change status of a fulfilled order.")
        self.order_status = new_status

    def __repr__(self):
        return f"<Order {self.order_id} - Status: {self.order_status.value}>"


class Payment:
    """Represents a payment transaction. (From Payment Management Component)"""
    def __init__(self, payment_id: int, order_id: int, amount: float):
        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.status = PaymentStatus.PENDING
        self.processed_at: Optional[datetime] = None

    def process_payment_simulation(self, success: bool = True):
        """Simulates payment processing (from Non-Functional Requirements)."""
        if success:
            self.status = PaymentStatus.SUCCESSFUL
        else:
            self.status = PaymentStatus.FAILED
        self.processed_at = datetime.now()
        return self.status


class Delivery:
    """Represents a delivery assignment. (From Class Diagram & Delivery Management Component)"""
    def __init__(self, delivery_id: int, order_id: int, driver_id: Optional[int], restaurant_address: str, customer_address: str):
        self.delivery_id = delivery_id
        self.order_id = order_id
        self.driver_id = driver_id
        self.restaurant_address = restaurant_address
        self.customer_address = customer_address
        self.status = DeliveryStatus.ASSIGNED if driver_id else None
        self.estimated_time: Optional[str] = None

    def update_delivery_status(self, new_status: DeliveryStatus):
        self.status = new_status
        # In a real system, this would trigger an update in the DB (Includes Update Database)

    def __repr__(self):
        return f"<Delivery {self.delivery_id} for Order {self.order_id}>"


# Simple in-memory "database" to represent the Database component
class SimpleDatabase:
    """Acts as the central Database component that other components interact with."""
    def __init__(self):
        self.users: dict[int, User] = {}
        self.restaurants: dict[int, Restaurant] = {}
        self.menu_items: dict[int, MenuItem] = {}
        self.orders: dict[int, Order] = {}
        self.payments: dict[int, Payment] = {}
        self.deliveries: dict[int, Delivery] = {}
        self._next_ids = {'user': 1, 'restaurant': 1, 'menu': 1, 'order': 1, 'payment': 1, 'delivery': 1}

    def get_next_id(self, entity_type: str) -> int:
        current_id = self._next_ids[entity_type]
        self._next_ids[entity_type] += 1
        return current_id
