"""Unit tests for Issue Order rejection (OrderRejectionServices).

Covers FR3, Sub-123 (driver reassignment), Sub-124 (cancel + refund).
"""

import pytest
from fastapi import HTTPException

from app.repositories.order_repo import OrderRepo
from app.services.issue61_order_rejection_services import OrderRejectionServices

PENDING_ORDER = {
    "id": "order-1",
    "customer_id": "user-1",
    "restaurant_id": "rest-1",
    "items": [],
    "delivery_address": "123 Main St",
    "status": "pending",
    "payment_status": None,
    "assigned_driver_id": "driver-1",
    "refund_issued": False,
}

ACCEPTED_ORDER = {**PENDING_ORDER, "id": "order-2", "status": "accepted"}


def _make_service(mocker, orders):
    mock_repo = mocker.Mock(spec=OrderRepo)
    mock_repo.load_all_orders.return_value = [dict(o) for o in orders]
    mock_repo.save_all_orders.return_value = None
    return OrderRejectionServices(mock_repo)


# ---------------------------------------------------------------------------
# Sub-124 – Restaurant owner rejection
# ---------------------------------------------------------------------------

def test_restaurant_reject_sets_status_cancelled(mocker):
    """Sub-124: Restaurant rejection sets status to 'cancelled'."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.restaurant_reject_order("order-1", "owner-1")
    assert result.status == "cancelled"


def test_restaurant_reject_issues_refund(mocker):
    """Sub-124: Restaurant rejection sets refund_issued to True."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.restaurant_reject_order("order-1", "owner-1")
    assert result.refund_issued is True


def test_restaurant_reject_accepted_order(mocker):
    """Restaurant owner can reject an already-accepted order."""
    service = _make_service(mocker, [dict(ACCEPTED_ORDER)])
    result = service.restaurant_reject_order("order-2", "owner-1")
    assert result.status == "cancelled"
    assert result.refund_issued is True


def test_restaurant_reject_fulfilled_order_raises_422(mocker):
    """Rejecting a fulfilled order raises 422."""
    fulfilled = {**PENDING_ORDER, "status": "fulfilled"}
    service = _make_service(mocker, [fulfilled])
    with pytest.raises(HTTPException) as exc_info:
        service.restaurant_reject_order("order-1", "owner-1")
    assert exc_info.value.status_code == 422


def test_restaurant_reject_cancelled_order_raises_422(mocker):
    """Rejecting an already-cancelled order raises 422."""
    cancelled = {**PENDING_ORDER, "status": "cancelled"}
    service = _make_service(mocker, [cancelled])
    with pytest.raises(HTTPException) as exc_info:
        service.restaurant_reject_order("order-1", "owner-1")
    assert exc_info.value.status_code == 422


def test_restaurant_reject_nonexistent_order_raises_404(mocker):
    """Rejecting a non-existent order raises 404."""
    service = _make_service(mocker, [])
    with pytest.raises(HTTPException) as exc_info:
        service.restaurant_reject_order("ghost", "owner-1")
    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Sub-123 – Driver rejection and reassignment
# ---------------------------------------------------------------------------

def test_driver_reject_reassigns_to_next_driver(mocker):
    """Sub-123: Rejection reassigns to the first available driver."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.driver_reject_order(
        "order-1", "driver-1", available_driver_ids=["driver-2", "driver-3"]
    )
    assert result.assigned_driver_id == "driver-2"


def test_driver_reject_skips_rejecting_driver_in_list(mocker):
    """Sub-123: The rejecting driver is not reassigned."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.driver_reject_order(
        "order-1", "driver-1", available_driver_ids=["driver-1", "driver-2"]
    )
    assert result.assigned_driver_id == "driver-2"


def test_driver_reject_no_drivers_reverts_to_pending(mocker):
    """Sub-123: No available drivers → order reverts to 'pending'."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.driver_reject_order("order-1", "driver-1", available_driver_ids=[])
    assert result.assigned_driver_id is None
    assert result.status == "pending"


def test_driver_reject_none_available_reverts_to_pending(mocker):
    """Sub-123: available_driver_ids=None → order reverts to 'pending'."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.driver_reject_order("order-1", "driver-1", available_driver_ids=None)
    assert result.status == "pending"


def test_driver_reject_with_reassignment_keeps_accepted_status(mocker):
    """Sub-123: Reassigned order remains 'accepted' for the new driver."""
    service = _make_service(mocker, [dict(ACCEPTED_ORDER)])
    result = service.driver_reject_order(
        "order-2", "driver-1", available_driver_ids=["driver-2"]
    )
    assert result.status == "accepted"
    assert result.assigned_driver_id == "driver-2"


def test_driver_reject_fulfilled_order_raises_422(mocker):
    """Rejecting a fulfilled order raises 422."""
    fulfilled = {**PENDING_ORDER, "status": "fulfilled"}
    service = _make_service(mocker, [fulfilled])
    with pytest.raises(HTTPException) as exc_info:
        service.driver_reject_order("order-1", "driver-1")
    assert exc_info.value.status_code == 422


def test_driver_reject_nonexistent_order_raises_404(mocker):
    """Rejecting a non-existent order raises 404."""
    service = _make_service(mocker, [])
    with pytest.raises(HTTPException) as exc_info:
        service.driver_reject_order("ghost", "driver-1")
    assert exc_info.value.status_code == 404
  
