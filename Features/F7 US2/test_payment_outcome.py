"""Unit tests for Payment outcome messages (PaymentOutcomeServices)."""

from datetime import datetime

import pytest
from fastapi import HTTPException

from app.repositories.order_repo import OrderRepo
from app.schemas.issue42_payment_outcome_schema import PaymentOutcomeRequest
from app.services.issue42_payment_outcome_services import PaymentOutcomeServices

FUTURE_YEAR = datetime.now().year + 2

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
    return PaymentOutcomeServices(mock_repo)


def _valid_payload():
    return PaymentOutcomeRequest(
        order_id="order-1",
        customer_id="user-1",
        card_number="4111111111111111",
        cvv="123",
        expiry_month=1,
        expiry_year=FUTURE_YEAR,
    )


# ---------------------------------------------------------------------------
# Success message tests (US2)
# ---------------------------------------------------------------------------

def test_accepted_payment_message_is_not_empty(mocker):
    """US2: Accepted payment includes a non-empty message."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.process_and_notify(_valid_payload())
    assert result.message != ""


def test_accepted_payment_message_indicates_success(mocker):
    """US2: Accepted payment message clearly communicates success."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.process_and_notify(_valid_payload())
    assert "accepted" in result.message.lower() or "confirmed" in result.message.lower()


def test_accepted_payment_status_is_accepted(mocker):
    """US2: Accepted payment returns payment_status 'accepted'."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.process_and_notify(_valid_payload())
    assert result.payment_status == "accepted"


def test_accepted_payment_order_status_is_paid(mocker):
    """US2: Accepted payment updates order_status to 'paid'."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.process_and_notify(_valid_payload())
    assert result.order_status == "paid"


# ---------------------------------------------------------------------------
# Failure message tests (US2)
# ---------------------------------------------------------------------------

def test_rejected_payment_message_is_not_empty(mocker):
    """US2: Rejected payment includes a non-empty message."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.cvv = "12"
    result = service.process_and_notify(p)
    assert result.message != ""


def test_rejected_payment_message_indicates_failure(mocker):
    """US2: Rejected payment message clearly communicates failure."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.card_number = "123"
    result = service.process_and_notify(p)
    assert "rejected" in result.message.lower()


def test_rejected_payment_message_includes_reason(mocker):
    """US2: Rejected payment message includes a reason for the customer."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.cvv = "12"
    result = service.process_and_notify(p)
    # Message should contain actionable guidance, not just "rejected"
    assert len(result.message) > len("Payment rejected.")


def test_rejected_payment_status_is_rejected(mocker):
    """US2: Rejected payment returns payment_status 'rejected'."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.cvv = "12"
    result = service.process_and_notify(p)
    assert result.payment_status == "rejected"


def test_rejected_payment_order_status_is_payment_failed(mocker):
    """US2: Rejected payment updates order_status to 'payment_failed'."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    p = _valid_payload()
    p.cvv = "12"
    result = service.process_and_notify(p)
    assert result.order_status == "payment_failed"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_order_not_found_raises_404(mocker):
    """Non-existent order raises 404."""
    service = _make_service(mocker, [])
    with pytest.raises(HTTPException) as exc_info:
        service.process_and_notify(_valid_payload())
    assert exc_info.value.status_code == 404


def test_already_paid_order_raises_422(mocker):
    """Order already paid raises 422."""
    paid = {**PENDING_ORDER, "status": "paid"}
    service = _make_service(mocker, [paid])
    with pytest.raises(HTTPException) as exc_info:
        service.process_and_notify(_valid_payload())
    assert exc_info.value.status_code == 422


def test_cancelled_order_raises_422(mocker):
    """Cancelled order raises 422."""
    cancelled = {**PENDING_ORDER, "status": "cancelled"}
    service = _make_service(mocker, [cancelled])
    with pytest.raises(HTTPException) as exc_info:
        service.process_and_notify(_valid_payload())
    assert exc_info.value.status_code == 422
  
