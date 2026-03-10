"""Integration tests for Issue #61 – Order rejection endpoints."""

import json

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.order_repo import OrderRepo
from app.routers.issue61_order_rejection_router import create_order_repo

client = TestClient(app)

BASE_ORDER = {
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


def _override(tmp_path, orders=None):
    path = tmp_path / "orders.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(orders if orders is not None else [BASE_ORDER], f, ensure_ascii=False, indent=2)

    def override():
        return OrderRepo(path)

    app.dependency_overrides[create_order_repo] = override


# ---------------------------------------------------------------------------
# Sub-124 – Restaurant rejection
# ---------------------------------------------------------------------------

def test_restaurant_reject_returns_200(tmp_path):
    """POST /orders/{id}/reject/restaurant returns 200."""
    _override(tmp_path)
    r = client.post("/orders/order-1/reject/restaurant?owner_id=owner-1")
    assert r.status_code == 200


def test_restaurant_reject_status_is_cancelled(tmp_path):
    """Sub-124: Restaurant rejection sets status to 'cancelled'."""
    _override(tmp_path)
    r = client.post("/orders/order-1/reject/restaurant?owner_id=owner-1")
    assert r.json()["status"] == "cancelled"


def test_restaurant_reject_refund_is_issued(tmp_path):
    """Sub-124: Restaurant rejection sets refund_issued to True."""
    _override(tmp_path)
    r = client.post("/orders/order-1/reject/restaurant?owner_id=owner-1")
    assert r.json()["refund_issued"] is True


def test_restaurant_reject_nonexistent_order_returns_404(tmp_path):
    """POST returns 404 for unknown order."""
    _override(tmp_path, orders=[])
    r = client.post("/orders/ghost/reject/restaurant?owner_id=owner-1")
    assert r.status_code == 404


def test_restaurant_reject_fulfilled_order_returns_422(tmp_path):
    """POST returns 422 when order is fulfilled."""
    _override(tmp_path, orders=[{**BASE_ORDER, "status": "fulfilled"}])
    r = client.post("/orders/order-1/reject/restaurant?owner_id=owner-1")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Sub-123 – Driver rejection
# ---------------------------------------------------------------------------

def test_driver_reject_returns_200(tmp_path):
    """POST /orders/{id}/reject/driver returns 200."""
    _override(tmp_path)
    r = client.post(
        "/orders/order-1/reject/driver?driver_id=driver-1&available_driver_ids=driver-2"
    )
    assert r.status_code == 200


def test_driver_reject_reassigns_to_next_driver(tmp_path):
    """Sub-123: Driver rejection reassigns to driver-2."""
    _override(tmp_path)
    r = client.post(
        "/orders/order-1/reject/driver?driver_id=driver-1&available_driver_ids=driver-2"
    )
    assert r.json()["assigned_driver_id"] == "driver-2"


def test_driver_reject_no_drivers_reverts_to_pending(tmp_path):
    """Sub-123: No available drivers → order reverts to 'pending'."""
    _override(tmp_path)
    r = client.post("/orders/order-1/reject/driver?driver_id=driver-1")
    assert r.json()["status"] == "pending"
    assert r.json()["assigned_driver_id"] is None


def test_driver_reject_nonexistent_order_returns_404(tmp_path):
    """POST returns 404 for unknown order."""
    _override(tmp_path, orders=[])
    r = client.post("/orders/ghost/reject/driver?driver_id=driver-1")
    assert r.status_code == 404


def test_driver_reject_fulfilled_order_returns_422(tmp_path):
    """POST returns 422 when order is fulfilled."""
  
    _override(tmp_path, orders=[{**BASE_ORDER, "status": "fulfilled"}])
    r = client.post("/orders/order-1/reject/driver?driver_id=driver-1")
    assert r.status_code == 422
