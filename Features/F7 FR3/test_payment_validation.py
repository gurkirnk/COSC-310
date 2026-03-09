"""Unit tests for Issue Payment validation rules."""

from datetime import datetime

import pytest
from fastapi import HTTPException

from app.repositories.order_repo import OrderRepo
from app.schemas.issue38_payment_validation_schema import PaymentValidationRequest
from app.services.issue38_payment_validation_services import PaymentValidationServices

CURRENT_YEAR = datetime.now().year
CURRENT_MONTH = datetime.now().month
FUTURE_YEAR = CURRENT_YEAR + 2

PENDING_ORDER = {
    "id": "order-1",
    "customer_id": "user-1",
    "restaurant_id": "rest-1",
    "items": [],
    "delivery_address": "123 Main St",
    "status": "pending",
    "payment_status": None,
    "assigned_driver_id": None,
    "refund_issued": False,
}


def _make_service(mocker, orders):
    mock_repo = mocker.Mock(spec=OrderRepo)
    mock_repo.get_order_by_id.side_effect = lambda oid: next(
        (o for o in orders if o["id"] == oid), None
    )
    mock_repo.load_all_orders.return_value = [dict(o) for o in orders]
    mock_repo.save_all_orders.return_value = None
    return PaymentValidationServices(mock_repo)


def _valid_payload():
    return PaymentValidationRequest(
        order_id="order-1",
        customer_id="user-1",
        card_number="4111111111111111",
        cvv="123",
        expiry_month=1,
        expiry_year=FUTURE_YEAR,
    )


# ---------------------------------------------------------------------------
# Rule 1 – card number
# ---------------------------------------------------------------------------

def test_valid_card_number_is_accepted(mocker):
    """16-digit numeric card number passes rule 1."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.validate_and_process(_valid_payload())
    assert result.payment_status == "accepted"


def test_card_number_too_short_is_rejected(mocker):
    """Fewer than 16 digits is rejected."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.card_number = "411111111111"
    result = service.validate_and_process(p)
    assert result.payment_status == "rejected"
    assert result.rejection_reason != ""


def test_card_number_too_long_is_rejected(mocker):
    """More than 16 digits is rejected."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.card_number = "41111111111111119"
    result = service.validate_and_process(p)
    assert result.payment_status == "rejected"


def test_card_number_with_letters_is_rejected(mocker):
    """Non-numeric card number is rejected."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.card_number = "411111111111111A"
    result = service.validate_and_process(p)
    assert result.payment_status == "rejected"


# ---------------------------------------------------------------------------
# Rule 2 – CVV
# ---------------------------------------------------------------------------

def test_valid_cvv_is_accepted(mocker):
    """3-digit numeric CVV passes rule 2."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.validate_and_process(_valid_payload())
    assert result.payment_status == "accepted"


def test_cvv_too_short_is_rejected(mocker):
    """Fewer than 3 CVV digits is rejected."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.cvv = "12"
    result = service.validate_and_process(p)
    assert result.payment_status == "rejected"


def test_cvv_too_long_is_rejected(mocker):
    """More than 3 CVV digits is rejected."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.cvv = "1234"
    result = service.validate_and_process(p)
    assert result.payment_status == "rejected"


def test_cvv_with_letters_is_rejected(mocker):
    """Non-numeric CVV is rejected."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.cvv = "12A"
    result = service.validate_and_process(p)
    assert result.payment_status == "rejected"


# ---------------------------------------------------------------------------
# Rule 3 – expiry month
# ---------------------------------------------------------------------------

def test_expiry_month_zero_is_rejected(mocker):
    """Expiry month of 0 is rejected."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.expiry_month = 0
    result = service.validate_and_process(p)
    assert result.payment_status == "rejected"


def test_expiry_month_thirteen_is_rejected(mocker):
    """Expiry month of 13 is rejected."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.expiry_month = 13
    result = service.validate_and_process(p)
    assert result.payment_status == "rejected"


# ---------------------------------------------------------------------------
# Rule 4 – expiry date
# ---------------------------------------------------------------------------

def test_expired_card_year_is_rejected(mocker):
    """Card expired in a past year is rejected."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.expiry_year = CURRENT_YEAR - 1
    p.expiry_month = 1
    result = service.validate_and_process(p)
    assert result.payment_status == "rejected"


# ---------------------------------------------------------------------------
# Order status updates
# ---------------------------------------------------------------------------

def test_accepted_payment_sets_order_status_to_paid(mocker):
    """Accepted payment updates order_status to 'paid'."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.validate_and_process(_valid_payload())
    assert result.order_status == "paid"


def test_rejected_payment_sets_order_status_to_payment_failed(mocker):
    """Rejected payment updates order_status to 'payment_failed'."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.cvv = "12"
    result = service.validate_and_process(p)
    assert result.order_status == "payment_failed"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_order_not_found_raises_404(mocker):
    """Non-existent order raises 404."""
    service = _make_service(mocker, [])
    with pytest.raises(HTTPException) as exc_info:
        service.validate_and_process(_valid_payload())
    assert exc_info.value.status_code == 404


def test_already_paid_order_raises_422(mocker):
    """Attempting to pay an already-paid order raises 422."""
    paid = {**PENDING_ORDER, "status": "paid"}
    service = _make_service(mocker, [paid])
    with pytest.raises(HTTPException) as exc_info:
        service.validate_and_process(_valid_payload())
    assert exc_info.value.status_code == 422
  
