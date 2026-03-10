"""Service layer for Payment outcome notification.

F7 US2: As a customer, I want to know whether my payment was accepted or rejected
     so that I know if my order was successful.

This service builds on the validation rules from Issue #38 and focuses on:
  - Producing a clear, human-readable success or failure message for the customer.
  - Updating the order status so it reflects the payment outcome.
"""

from datetime import datetime

from fastapi import HTTPException

from app.repositories.order_repo import OrderRepo
from app.schemas.issue42_payment_outcome_schema import (
    PaymentOutcomeRequest,
    PaymentOutcomeResponse,
)

CARD_NUMBER_LENGTH = 16
CVV_LENGTH = 3


class PaymentOutcomeServices:
    """Processes a payment and returns a clear outcome message to the customer."""

    def __init__(self, order_repo: OrderRepo):
        self.order_repo = order_repo

    def process_and_notify(
        self, payload: PaymentOutcomeRequest
    ) -> PaymentOutcomeResponse:
        """Process payment and return a clear accepted or rejected message.

        On success  → order status updated to 'paid',
                       customer receives a confirmation message.
        On failure  → order status updated to 'payment_failed',
                       customer receives a clear failure message explaining why.

        Raises:
            HTTPException 404 if the order does not exist.
            HTTPException 422 if the order is not in a payable state.
        """
        order = self.order_repo.get_order_by_id(payload.order_id)
        if order is None:
            raise HTTPException(
                status_code=404,
                detail=f"Order '{payload.order_id}' not found.",
            )

        if order["status"] not in ("pending", "accepted"):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Order '{payload.order_id}' cannot be paid. "
                    f"Current status: '{order['status']}'."
                ),
            )

        failure_reason = self._validate_card(payload)

        if failure_reason:
            self._update_order(payload.order_id, "payment_failed", "rejected")
            return PaymentOutcomeResponse(
                order_id=payload.order_id,
                payment_status="rejected",
                order_status="payment_failed",
                message=(
                    f"Payment rejected. {failure_reason} "
                    "Please check your card details and try again."
                ),
            )

        self._update_order(payload.order_id, "paid", "accepted")
        return PaymentOutcomeResponse(
            order_id=payload.order_id,
            payment_status="accepted",
            order_status="paid",
            message=(
                "Payment accepted! Your order has been confirmed and "
                "is now being prepared."
            ),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_card(self, payload: PaymentOutcomeRequest) -> str:
        """Return a failure reason string, or empty string if all rules pass."""
        if not payload.card_number.isdigit():
            return "Card number must contain digits only."
        if len(payload.card_number) != CARD_NUMBER_LENGTH:
            return f"Card number must be exactly {CARD_NUMBER_LENGTH} digits."
        if not payload.cvv.isdigit():
            return "CVV must contain digits only."
        if len(payload.cvv) != CVV_LENGTH:
            return f"CVV must be exactly {CVV_LENGTH} digits."
        if not (1 <= payload.expiry_month <= 12):
            return "Expiry month must be between 1 and 12."

        now = datetime.now()
        if payload.expiry_year < now.year or (
            payload.expiry_year == now.year and payload.expiry_month < now.month
        ):
            return "Card has expired."

        return ""

    def _update_order(
        self, order_id: str, new_status: str, payment_status: str
    ) -> None:
        """Persist updated order status fields."""
        orders = self.order_repo.load_all_orders()
        for i, o in enumerate(orders):
            if o["id"] == order_id:
                orders[i]["status"] = new_status
                orders[i]["payment_status"] = payment_status
                break
        self.order_repo.save_all_orders(orders)
      
