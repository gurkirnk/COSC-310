"""Integration tests for F7 US2 POST /payments (payment outcome messages)."""

import json
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.order_repo import OrderRepo
from app.routers.issue42_payment_outcome_router import create_order_repo

client = TestClient(app)

FUTURE_YEAR = datetime.now().year + 2

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

VALID_PAYLOAD = {
    "order_id": "order-1",
    "customer_id": "user-1",
    "card_number": "4111111111111111",
    "cvv": "123",
    "expiry_month": 1,
    "expiry_year": FUTURE_YEAR,
}


def _override(tmp_path, orders=None):
    path = tmp_path / "orders.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(orders if orders is not None else [BASE_ORDER], f, ensure_ascii=False, indent=2)

    def override():
        return OrderRepo(path)

    app.dependency_overrides[create_order_repo] = override


def test_accepted_payment_returns_200(tmp_path):
    """POST /payments returns 200 for a valid payment."""
    _override(tmp_path)
    r = client.post("/payments", json=VALID_PAYLOAD)
    assert r.status_code == 200


def test_accepted_payment_has_success_message(tmp_path):
    """US2: Accepted payment response contains a success message."""
    _override(tmp_path)
    r = client.post("/payments", json=VALID_PAYLOAD)
    msg = r.json()["message"].lower()
    assert "accepted" in msg or "confirmed" in msg


def test_accepted_payment_order_status_is_paid(tmp_path):
    """US2: Accepted payment sets order_status to 'paid'."""
    _override(tmp_path)
    r = client.post("/payments", json=VALID_PAYLOAD)
    assert r.json()["order_status"] == "paid"


def test_rejected_payment_has_failure_message(tmp_path):
    """US2: Rejected payment response contains a failure message."""
    _override(tmp_path)
    r = client.post("/payments", json={**VALID_PAYLOAD, "cvv": "12"})
    assert "rejected" in r.json()["message"].lower()


def test_rejected_payment_order_status_is_payment_failed(tmp_path):
    """US2: Rejected payment sets order_status to 'payment_failed'."""
    _override(tmp_path)
    r = client.post("/payments", json={**VALID_PAYLOAD, "cvv": "12"})
    assert r.json()["order_status"] == "payment_failed"


def test_response_contains_message_field(tmp_path):
    """US2: Response always contains a message field."""
    _override(tmp_path)
    r = client.post("/payments", json=VALID_PAYLOAD)
    assert "message" in r.json()
    assert r.json()["message"] != ""


def test_order_not_found_returns_404(tmp_path):
    """POST /payments returns 404 for an unknown order."""
    _override(tmp_path, orders=[])
    r = client.post("/payments", json=VALID_PAYLOAD)
    assert r.status_code == 404


def test_response_schema_has_all_fields(tmp_path):
    """Response contains all required fields."""
    _override(tmp_path)
    r = client.post("/payments", json=VALID_PAYLOAD)
    for field in ("order_id", "payment_status", "order_status", "message"):
        assert field in r.json()
      
