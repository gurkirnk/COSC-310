"""Unit tests for Restaurant owner order management (RestaurantOrderServices)."""

import pytest
from fastapi import HTTPException

from app.repositories.order_repo import OrderRepo
from app.services.issue65_restaurant_order_services import RestaurantOrderServices

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
    return RestaurantOrderServices(mock_repo)


# ---------------------------------------------------------------------------
# get_pending_order – popup display
# ---------------------------------------------------------------------------

def test_get_pending_order_returns_all_fields(mocker):
    """get_pending_order returns full order details for the popup."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.get_pending_order("order-1")
    assert result.id == "order-1"
    assert result.customer_id == "user-1"
    assert result.restaurant_id == "rest-1"
    assert result.delivery_address == "123 Main St"
    assert result.status == "pending"


def test_get_pending_order_not_found_raises_404(mocker):
    """get_pending_order raises 404 for unknown order."""
    service = _make_service(mocker, [])
    with pytest.raises(HTTPException) as exc_info:
        service.get_pending_order("ghost")
    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# accept_order
# ---------------------------------------------------------------------------

def test_accept_order_sets_status_to_accepted(mocker):
    """accept_order sets the order status to 'accepted'."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.accept_order("order-1", "owner-1")
    assert result.new_status == "accepted"
    assert result.action == "accepted"


def test_accept_order_refund_is_false(mocker):
    """accept_order does not issue a refund."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.accept_order("order-1", "owner-1")
    assert result.refund_issued is False


def test_accept_order_returns_confirmation_message(mocker):
    """accept_order response contains a non-empty confirmation message."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.accept_order("order-1", "owner-1")
    assert result.message != ""


def test_accept_nonexistent_order_raises_404(mocker):
    """accept_order raises 404 for unknown order."""
    service = _make_service(mocker, [])
    with pytest.raises(HTTPException) as exc_info:
        service.accept_order("ghost", "owner-1")
    assert exc_info.value.status_code == 404


def test_accept_already_accepted_order_raises_422(mocker):
    """Accepting an already-accepted order raises 422."""
    accepted = {**PENDING_ORDER, "status": "accepted"}
    service = _make_service(mocker, [accepted])
    with pytest.raises(HTTPException) as exc_info:
        service.accept_order("order-1", "owner-1")
    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# reject_order – US2 + Sub-124
# ---------------------------------------------------------------------------

def test_reject_order_sets_status_to_cancelled(mocker):
    """US2: reject_order sets the order status to 'cancelled'."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.reject_order("order-1", "owner-1")
    assert result.new_status == "cancelled"
    assert result.action == "rejected"


def test_reject_order_issues_refund(mocker):
    """Sub-124: reject_order sets refund_issued to True."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.reject_order("order-1", "owner-1")
    assert result.refund_issued is True


def test_reject_order_returns_confirmation_message(mocker):
    """US2: reject_order response contains a non-empty message."""
    service = _make_service(mocker, [dict(PENDING_ORDER)])
    result = service.reject_order("order-1", "owner-1")
    assert result.message != ""
    assert "refund" in result.message.lower() or "rejected" in result.message.lower()


def test_reject_nonexistent_order_raises_404(mocker):
    """reject_order raises 404 for unknown order."""
    service = _make_service(mocker, [])
    with pytest.raises(HTTPException) as exc_info:
        service.reject_order("ghost", "owner-1")
    assert exc_info.value.status_code == 404


def test_reject_cancelled_order_raises_422(mocker):
    """Rejecting an already-cancelled order raises 422."""
    cancelled = {**PENDING_ORDER, "status": "cancelled"}
    service = _make_service(mocker, [cancelled])
    with pytest.raises(HTTPException) as exc_info:
        service.reject_order("order-1", "owner-1")
    assert exc_info.value.status_code == 422


def test_reject_fulfilled_order_raises_422(mocker):
    """Rejecting a fulfilled order raises 422."""
    fulfilled = {**PENDING_ORDER, "status": "fulfilled"}
    service = _make_service(mocker, [fulfilled])
    with pytest.raises(HTTPException) as exc_info:
        service.reject_order("order-1", "owner-1")
    assert exc_info.value.status_code == 422
  
