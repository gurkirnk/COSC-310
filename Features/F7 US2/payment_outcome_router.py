"""Payment outcome API endpoint.

POST /payments  — process a payment and return a clear success or failure
                  message to the customer.
"""

from pathlib import Path

from fastapi import APIRouter, Depends

from app.repositories.order_repo import OrderRepo
from app.schemas.issue42_payment_outcome_schema import (
    PaymentOutcomeRequest,
    PaymentOutcomeResponse,
)
from app.services.issue42_payment_outcome_services import PaymentOutcomeServices

payment_outcome_router = APIRouter(prefix="/payments", tags=["payment"])

ORDER_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.json"


def create_order_repo() -> OrderRepo:
    """Initialize OrderRepo with the orders JSON file path."""
    return OrderRepo(ORDER_DATA_PATH)


@payment_outcome_router.post(
    "",
    response_model=PaymentOutcomeResponse,
    status_code=200,
)
def process_payment(
    payload: PaymentOutcomeRequest,
    order_repo: OrderRepo = Depends(create_order_repo),
):
    """Process a payment and return a clear outcome message to the customer.

    On success the customer sees a confirmation and the order status is set
    to 'paid'. On failure the customer sees a clear rejection message and
    the order status is set to 'payment_failed'.
    Returns 404 if the order does not exist.
    Returns 422 if the order is not in a payable state.
    """
    service = PaymentOutcomeServices(order_repo)
    return service.process_and_notify(payload)
  
