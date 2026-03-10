"""Pydantic schemas for Restaurant owner order management.

F4 US2: As a restaurant owner/manager, I want to be able to reject orders so that
     in the case where we are not able to fulfill a request the order will not
     go through.

Acceptance criteria: A popup shows full order details with accept/reject buttons.
"""

from typing import List, Optional
from pydantic import BaseModel


class OrderItem(BaseModel):
    """A single item within an order."""
    menu_item_id: str
    name: str
    price: float
    quantity: int


class OrderDetails(BaseModel):
    """Full order details displayed in the restaurant owner's popup."""
    id: str
    customer_id: str
    restaurant_id: str
    items: List[OrderItem]
    delivery_address: str
    status: str
    payment_status: Optional[str] = None
    assigned_driver_id: Optional[str] = None
    refund_issued: bool = False


class RestaurantOrderActionResponse(BaseModel):
    """Response returned after a restaurant owner accepts or rejects an order."""
    order_id: str
    action: str          # "accepted" or "rejected"
    new_status: str      # updated order status
    refund_issued: bool  # True only when rejected (Sub-124)
    message: str         # Confirmation message shown to the restaurant owner
