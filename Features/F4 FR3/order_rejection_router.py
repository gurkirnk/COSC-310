"""Order rejection API endpoints – Issue #61.

POST /orders/{order_id}/reject/restaurant  — restaurant owner rejects an order.
POST /orders/{order_id}/reject/driver      — delivery driver rejects an order.
"""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.repositories.order_repo import OrderRepo
from app.schemas.issue61_order_rejection_schema import DriverRejectRequest, Order
from app.services.issue61_order_rejection_services import OrderRejectionServices

order_rejection_router = APIRouter(prefix="/orders", tags=["order"])

ORDER_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.json"


def create_order_repo() -> OrderRepo:
    """Initialize OrderRepo with the orders JSON file path."""
    return OrderRepo(ORDER_DATA_PATH)


@order_rejection_router.post(
    "/{order_id}/reject/restaurant",
    response_model=Order,
    status_code=200,
)
def restaurant_reject_order(
    order_id: str,
    owner_id: str = Query(..., description="ID of the restaurant owner rejecting the order"),
    order_repo: OrderRepo = Depends(create_order_repo),
):
    """Restaurant owner rejects an order.

    Sub-124: Cancels the order and marks a refund as issued.
    Returns 404 if the order does not exist.
    Returns 422 if the order is not in a rejectable status.
    """
    service = OrderRejectionServices(order_repo)
    return service.restaurant_reject_order(order_id, owner_id)


@order_rejection_router.post(
    "/{order_id}/reject/driver",
    response_model=Order,
    status_code=200,
)
def driver_reject_order(
    order_id: str,
    driver_id: str = Query(..., description="ID of the driver rejecting the order"),
    available_driver_ids: Optional[List[str]] = Query(
        default=None,
        description="Ordered list of other available driver IDs for reassignment",
    ),
    order_repo: OrderRepo = Depends(create_order_repo),
):
    """Delivery driver rejects an assigned order.

    Sub-123: Reassigns the order to the next available driver.
    If no other drivers are available the order reverts to 'pending'.
    Returns 404 if the order does not exist.
    Returns 422 if the order is not in a rejectable status.
    """
    service = OrderRejectionServices(order_repo)
    return service.driver_reject_order(order_id, driver_id, available_driver_ids)
  
