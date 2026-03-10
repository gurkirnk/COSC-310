"""Integration tests for Restaurant owner order management endpoints."""

import json

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.order_repo import OrderRepo
from app.routers.issue65_restaurant_order_router import create_order_repo

client = TestClient(app)

BASE_ORDER = {
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


def _override(tmp_path, orders=None):
    path = tmp_path / "orders.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(orders if orders is not None else [BASE_ORDER], f, ensure_ascii=False, indent=2)

    def override():
        return OrderRepo(path)

    app.dependency_overrides[create_order_repo] = override


# ---------------------------------------------------------------------------
# GET popup details
# ---------------------------------------------------------------------------

def test_get_order_for_popup_returns_200(tmp_path):
    """GET /restaurants/{rid}/orders/{oid} returns 200."""
    _override(tmp_path)
    r = client.get("/restaurants/rest-1/orders/order-1")
    assert r.status_code == 200


def test_get_order_for_popup_contains_all_fields(tmp_path):
    """Popup response contains all fields needed for display."""
    _override(tmp_path)
    r = client.get("/restaurants/rest-1/orders/order-1")
    data = r.json()
    for field in ("id", "customer_id", "restaurant_id", "items",
                  "delivery_address", "status"):
        assert field in data


def test_get_order_for_popup_not_found_returns_404(tmp_path):
    """GET returns 404 for unknown order."""
    _override(tmp_path, orders=[])
    r = client.get("/restaurants/rest-1/orders/ghost")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST accept
# ---------------------------------------------------------------------------

def test_accept_order_returns_200(tmp_path):
    """POST /accept returns 200."""
    _override(tmp_path)
    r = client.post("/restaurants/rest-1/orders/order-1/accept?owner_id=owner-1")
    assert r.status_code == 200


def test_accept_order_new_status_is_accepted(tmp_path):
    """POST /accept sets new_status to 'accepted'."""
    _override(tmp_path)
    r = client.post("/restaurants/rest-1/orders/order-1/accept?owner_id=owner-1")
    assert r.json()["new_status"] == "accepted"
    assert r.json()["action"] == "accepted"


def test_accept_order_refund_is_false(tmp_path):
    """POST /accept does not issue a refund."""
    _override(tmp_path)
    r = client.post("/restaurants/rest-1/orders/order-1/accept?owner_id=owner-1")
    assert r.json()["refund_issued"] is False


def test_accept_order_response_has_message(tmp_path):
    """POST /accept response contains a non-empty message."""
    _override(tmp_path)
    r = client.post("/restaurants/rest-1/orders/order-1/accept?owner_id=owner-1")
    assert r.json()["message"] != ""


def test_accept_nonexistent_order_returns_404(tmp_path):
    """POST /accept returns 404 for unknown order."""
    _override(tmp_path, orders=[])
    r = client.post("/restaurants/rest-1/orders/ghost/accept?owner_id=owner-1")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST reject
# ---------------------------------------------------------------------------

def test_reject_order_returns_200(tmp_path):
    """POST /reject returns 200."""
    _override(tmp_path)
    r = client.post("/restaurants/rest-1/orders/order-1/reject?owner_id=owner-1")
    assert r.status_code == 200


def test_reject_order_new_status_is_cancelled(tmp_path):
    """US2: POST /reject sets new_status to 'cancelled'."""
    _override(tmp_path)
    r = client.post("/restaurants/rest-1/orders/order-1/reject?owner_id=owner-1")
    assert r.json()["new_status"] == "cancelled"
    assert r.json()["action"] == "rejected"


def test_reject_order_refund_is_issued(tmp_path):
    """Sub-124: POST /reject sets refund_issued to True."""
    _override(tmp_path)
    r = client.post("/restaurants/rest-1/orders/order-1/reject?owner_id=owner-1")
    assert r.json()["refund_issued"] is True


def test_reject_order_response_has_message(tmp_path):
    """US2: POST /reject response contains a non-empty message."""
    _override(tmp_path)
    r = client.post("/restaurants/rest-1/orders/order-1/reject?owner_id=owner-1")
    assert r.json()["message"] != ""


def test_reject_nonexistent_order_returns_404(tmp_path):
    """POST /reject returns 404 for unknown order."""
    _override(tmp_path, orders=[])
    r = client.post("/restaurants/rest-1/orders/ghost/reject?owner_id=owner-1")
    assert r.status_code == 404


def test_reject_fulfilled_order_returns_422(tmp_path):
    """POST /reject returns 422 when order is fulfilled."""
    _override(tmp_path, orders=[{**BASE_ORDER, "status": "fulfilled"}])
    r = client.post("/restaurants/rest-1/orders/order-1/reject?owner_id=owner-1")
    assert r.status_code == 422
  
