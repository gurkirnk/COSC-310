"""Service layer for Restaurant owner order management.

F4 US2: As a restaurant owner/manager, I want to be able to reject orders so that
     in the case where we are not able to fulfill a request the order will not
     go through.

Provides:
  - get_pending_order: fetches full order details for the popup display.
  - accept_order:      owner accepts an incoming order.
  - reject_order:      owner rejects → order cancelled, refund issued (Sub-124).
"""

from typing import Any, Dict, List

from fastapi import HTTPException

from app.repositories.order_repo import OrderRepo
from app.schemas.issue65_restaurant_order_schema import (
    OrderDetails,
    RestaurantOrderActionResponse,
)

ACTIONABLE_STATUSES = ("pending",)


class RestaurantOrderServices:
    """Handles order accept/reject actions for restaurant owners."""

    def __init__(self, order_repo: OrderRepo):
        self.order_repo = order_repo

    def get_pending_order(self, order_id: str) -> OrderDetails:
        """Return full order details so the owner can review them in a popup.

        Raises:
            HTTPException 404 if the order does not exist.
        """
        order = self.order_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=404,
                detail=f"Order '{order_id}' not found.",
            )
        return OrderDetails(**order)

    def accept_order(
        self, order_id: str, owner_id: str
    ) -> RestaurantOrderActionResponse:
        """Restaurant owner accepts an incoming order.

        Sets order status to 'accepted'.

        Raises:
            HTTPException 404 if the order does not exist.
            HTTPException 422 if the order is not in 'pending' status.
        """
        orders = self.order_repo.load_all_orders()
        order, idx = self._find_order(orders, order_id)
        self._assert_actionable(order)

        orders[idx]["status"] = "accepted"
        self.order_repo.save_all_orders(orders)

        return RestaurantOrderActionResponse(
            order_id=order_id,
            action="accepted",
            new_status="accepted",
            refund_issued=False,
            message="Order accepted. Preparation can begin.",
        )

    def reject_order(
        self, order_id: str, owner_id: str
    ) -> RestaurantOrderActionResponse:
        """Restaurant owner rejects an incoming order.

        Sub-124: Sets order status to 'cancelled' and issues a refund.

        Raises:
            HTTPException 404 if the order does not exist.
            HTTPException 422 if the order is not in 'pending' status.
        """
        orders = self.order_repo.load_all_orders()
        order, idx = self._find_order(orders, order_id)
        self._assert_actionable(order)

        orders[idx]["status"] = "cancelled"
        orders[idx]["refund_issued"] = True
        self.order_repo.save_all_orders(orders)

        return RestaurantOrderActionResponse(
            order_id=order_id,
            action="rejected",
            new_status="cancelled",
            refund_issued=True,
            message="Order rejected. The customer will be refunded.",
        )

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

    def _assert_actionable(self, order: Dict[str, Any]) -> None:
        """Raise 422 if the order cannot be acted on in its current status."""
        if order["status"] not in ACTIONABLE_STATUSES:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Order '{order['id']}' cannot be accepted or rejected. "
                    f"Current status: '{order['status']}'."
                ),
            )
          
