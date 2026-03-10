"""Service layer for Order rejection by restaurant owner and driver.

FR3     : The system should allow restaurant owners and drivers to reject an order.
Sub-123 : When a delivery driver rejects an order it is moved to a new driver.
Sub-124 : When a restaurant owner rejects an order it is cancelled and a refund issued.
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.repositories.order_repo import OrderRepo
from app.schemas.issue61_order_rejection_schema import Order

REJECTABLE_STATUSES = ("pending", "accepted")


class OrderRejectionServices:
    """Handles order rejection for both restaurant owners and delivery drivers."""

    def __init__(self, order_repo: OrderRepo):
        self.order_repo = order_repo

    # ------------------------------------------------------------------
    # Restaurant owner rejection – Sub-124
    # ------------------------------------------------------------------

    def restaurant_reject_order(self, order_id: str, owner_id: str) -> Order:
        """Restaurant owner rejects an order.

        Sub-124: Sets order status to 'cancelled' and refund_issued to True.

        Raises:
            HTTPException 404 if the order does not exist.
            HTTPException 422 if the order is not in a rejectable status.
        """
        orders = self.order_repo.load_all_orders()
        order, idx = self._find_order(orders, order_id)
        self._assert_rejectable(order)

        orders[idx]["status"] = "cancelled"
        orders[idx]["refund_issued"] = True
        self.order_repo.save_all_orders(orders)

        return Order(**orders[idx])

    # ------------------------------------------------------------------
    # Delivery driver rejection – Sub-123
    # ------------------------------------------------------------------

    def driver_reject_order(
        self,
        order_id: str,
        driver_id: str,
        available_driver_ids: Optional[List[str]] = None,
    ) -> Order:
        """Delivery driver rejects an assigned order.

        Sub-123: Reassigns the order to the next available driver.
        If no other driver is available the order reverts to 'pending'
        with no assigned driver.

        Raises:
            HTTPException 404 if the order does not exist.
            HTTPException 422 if the order is not in a rejectable status.
        """
        orders = self.order_repo.load_all_orders()
        order, idx = self._find_order(orders, order_id)
        self._assert_rejectable(order)

        # Sub-123: pick the first candidate that is not the rejecting driver
        next_driver = None
        if available_driver_ids:
            candidates = [d for d in available_driver_ids if d != driver_id]
            if candidates:
                next_driver = candidates[0]

        orders[idx]["assigned_driver_id"] = next_driver
        orders[idx]["status"] = "accepted" if next_driver else "pending"
        self.order_repo.save_all_orders(orders)

        return Order(**orders[idx])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_order(
        self, orders: List[Dict[str, Any]], order_id: str
    ):
        """Return (order_dict, index) or raise 404."""
        for i, o in enumerate(orders):
            if o["id"] == order_id:
                return o, i
        raise HTTPException(
            status_code=404,
            detail=f"Order '{order_id}' not found.",
        )

    def _assert_rejectable(self, order: Dict[str, Any]) -> None:
        """Raise 422 if the order cannot be rejected in its current status."""
        if order["status"] not in REJECTABLE_STATUSES:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Order '{order['id']}' cannot be rejected. "
                    f"Current status: '{order['status']}'."
                ),
            )
          
