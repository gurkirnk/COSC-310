"""Payment validation API endpoint.

POST /payments/validate  — apply pre-defined rules to a payment attempt.
"""

from pathlib import Path

from fastapi import APIRouter, Depends

from app.repositories.order_repo import OrderRepo
from app.schemas.issue38_payment_validation_schema import (
    PaymentValidationRequest,
    PaymentValidationResponse,
)
from app.services.issue38_payment_validation_services import PaymentValidationServices

payment_validation_router = APIRouter(prefix="/payments", tags=["payment"])

ORDER_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.json"


def create_order_repo() -> OrderRepo:
    """Initialize OrderRepo with the orders JSON file path."""
    return OrderRepo(ORDER_DATA_PATH)


@payment_validation_router.post(
    "/validate",
    response_model=PaymentValidationResponse,
    status_code=200,
)
def validate_payment(
    payload: PaymentValidationRequest,
    order_repo: OrderRepo = Depends(create_order_repo),
):
    """Validate a payment attempt using pre-defined rules.

    Rules checked:
      - card_number must be exactly 16 numeric digits
      - cvv must be exactly 3 numeric digits
      - expiry_month must be 1–12
      - card must not have already expired

    Returns payment_status of 'accepted' or 'rejected' and the updated
    order_status. Returns 404 if the order does not exist.
    Returns 422 if the order is not in a payable state.
    """
    service = PaymentValidationServices(order_repo)
    return service.validate_and_process(payload)
  
