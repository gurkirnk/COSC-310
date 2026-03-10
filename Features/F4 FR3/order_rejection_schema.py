"""Pydantic schemas for Order rejection by restaurant owner and driver.

FR3     : The system should allow restaurant owners and drivers to reject an order.
Sub-123 : When a delivery driver rejects, the order is reassigned to a new driver.
Sub-124 : When a restaurant owner rejects, the order is cancelled and a refund issued.
"""

from typing import List, Optional
from pydantic import BaseModel


class OrderItem(BaseModel):
    """A single item within an order."""
    menu_item_id: str
    name: str
    price: float
    quantity: int


class Order(BaseModel):
    """Full order entity."""
    id: str
    customer_id: str
    restaurant_id: str
    items: List[OrderItem]
    delivery_address: str
    status: str = "pending"
    payment_status: Optional[str] = None
    assigned_driver_id: Optional[str] = None
    refund_issued: bool = False


class DriverRejectRequest(BaseModel):
    """Payload for a driver rejecting an order.

    available_driver_ids: ordered list of other drivers to try next (Sub-123).
    """
    driver_id: str
    available_driver_ids: Optional[List[str]] = None
  
