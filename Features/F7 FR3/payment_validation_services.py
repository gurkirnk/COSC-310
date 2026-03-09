"""Service layer for Payment validation rules.

FR3: The system shall determine whether a payment is accepted or rejected
     based on pre-defined rules.

Pre-defined rules:
  1. card_number must be exactly 16 numeric digits.
  2. cvv must be exactly 3 numeric digits.
  3. expiry_month must be between 1 and 12 inclusive.
  4. The card must not have already expired (expiry_year/month vs today).
"""

from datetime import datetime

from fastapi import HTTPException

from app.repositories.order_repo import OrderRepo
from app.schemas.issue38_payment_validation_schema import (
    PaymentValidationRequest,
    PaymentValidationResponse,
)

CARD_NUMBER_LENGTH = 16
CVV_LENGTH = 3
EXPIRY_MONTH_MIN = 1
EXPIRY_MONTH_MAX = 12


class PaymentValidationServices:
    """Validates card details against pre-defined rules and updates order status."""

    def __init__(self, order_repo: OrderRepo):
        self.order_repo = order_repo

    def validate_and_process(
        self, payload: PaymentValidationRequest
    ) -> PaymentValidationResponse:
        """Apply all pre-defined validation rules to a payment attempt.

        Exactly one of two outcomes is produced (FR3):
          - Accepted: all rules pass  → payment_status="accepted", order_status="paid"
          - Rejected: any rule fails  → payment_status="rejected", order_status="payment_failed"

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

        rejection_reason = self._run_rules(payload)

        if rejection_reason:
            self._update_order(payload.order_id, "payment_failed", "rejected")
            return PaymentValidationResponse(
                order_id=payload.order_id,
                payment_status="rejected",
                order_status="payment_failed",
                rejection_reason=rejection_reason,
            )

        self._update_order(payload.order_id, "paid", "accepted")
        return PaymentValidationResponse(
            order_id=payload.order_id,
            payment_status="accepted",
            order_status="paid",
            rejection_reason="",
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_rules(self, payload: PaymentValidationRequest) -> str:
        """Run every pre-defined rule in order.

        Returns an empty string when all rules pass, or the first
        human-readable rejection reason encountered.
        """
        # Rule 1 – card number: exactly 16 numeric digits
        if not payload.card_number.isdigit():
            return "Card number must contain digits only."
        if len(payload.card_number) != CARD_NUMBER_LENGTH:
            return (
                f"Card number must be exactly {CARD_NUMBER_LENGTH} digits "
                f"(received {len(payload.card_number)})."
            )

        # Rule 2 – CVV: exactly 3 numeric digits
        if not payload.cvv.isdigit():
            return "CVV must contain digits only."
        if len(payload.cvv) != CVV_LENGTH:
            return (
                f"CVV must be exactly {CVV_LENGTH} digits "
                f"(received {len(payload.cvv)})."
            )

        # Rule 3 – expiry month: 1–12
        if not (EXPIRY_MONTH_MIN <= payload.expiry_month <= EXPIRY_MONTH_MAX):
            return (
                f"Expiry month must be between {EXPIRY_MONTH_MIN} "
                f"and {EXPIRY_MONTH_MAX}."
            )

        # Rule 4 – card must not be expired
        now = datetime.now()
        if payload.expiry_year < now.year or (
            payload.expiry_year == now.year
            and payload.expiry_month < now.month
        ):
            return "Card has expired."

        return ""

    def _update_order(
        self, order_id: str, new_status: str, payment_status: str
    ) -> None:
        """Persist updated status fields to the order store."""
        orders = self.order_repo.load_all_orders()
        for i, o in enumerate(orders):
            if o["id"] == order_id:
                orders[i]["status"] = new_status
                orders[i]["payment_status"] = payment_status
                break
        self.order_repo.save_all_orders(orders)
      
