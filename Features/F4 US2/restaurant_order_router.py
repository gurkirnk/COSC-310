"""Restaurant order management API endpoints.

GET  /restaurants/{restaurant_id}/orders/{order_id}         — fetch order details for popup.
POST /restaurants/{restaurant_id}/orders/{order_id}/accept  — owner accepts the order.
POST /restaurants/{restaurant_id}/orders/{order_id}/reject  — owner rejects the order.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Query

from app.repositories.order_repo import OrderRepo
from app.schemas.issue65_restaurant_order_schema import (
    OrderDetails,
    RestaurantOrderActionResponse,
)
from app.services.issue65_restaurant_order_services import RestaurantOrderServices

restaurant_order_router = APIRouter(prefix="/restaurants", tags=["restaurant", "order"])

ORDER_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.json"


def create_order_repo() -> OrderRepo:
    """Initialize OrderRepo with the orders JSON file path."""
    return OrderRepo(ORDER_DATA_PATH)


@restaurant_order_router.get(
    "/{restaurant_id}/orders/{order_id}",
    response_model=OrderDetails,
    status_code=200,
)
def get_order_for_popup(
    restaurant_id: str,
    order_id: str,
    order_repo: OrderRepo = Depends(create_order_repo),
):
    """Return full order details for the restaurant owner's popup.

    Provides everything the popup needs to show: items, delivery address,
    customer ID, and current status.
    Returns 404 if the order does not exist.
    """
    service = RestaurantOrderServices(order_repo)
    return service.get_pending_order(order_id)


@restaurant_order_router.post(
    "/{restaurant_id}/orders/{order_id}/accept",
    response_model=RestaurantOrderActionResponse,
    status_code=200,
)
def accept_order(
    restaurant_id: str,
    order_id: str,
    owner_id: str = Query(..., description="ID of the restaurant owner accepting the order"),
    order_repo: OrderRepo = Depends(create_order_repo),
):
    """Restaurant owner accepts an incoming order.

    Sets the order status to 'accepted'.
    Returns 404 if the order does not exist.
    Returns 422 if the order is not in 'pending' status.
    """
    service = RestaurantOrderServices(order_repo)
    return service.accept_order(order_id, owner_id)


@restaurant_order_router.post(
    "/{restaurant_id}/orders/{order_id}/reject",
    response_model=RestaurantOrderActionResponse,
    status_code=200,
)
def reject_order(
    restaurant_id: str,
    order_id: str,
    owner_id: str = Query(..., description="ID of the restaurant owner rejecting the order"),
    order_repo: OrderRepo = Depends(create_order_repo),
):
    """Restaurant owner rejects an incoming order.

    Sub-124: Cancels the order and issues a refund to the customer.
    Returns 404 if the order does not exist.
    Returns 422 if the order is not in 'pending' status.
    """
    service = RestaurantOrderServices(order_repo)
    return service.reject_order(order_id, owner_id)
  
