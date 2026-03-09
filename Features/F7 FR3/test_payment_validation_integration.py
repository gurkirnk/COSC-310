"""Integration tests for Issue #38 – POST /payments/validate."""

import json
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.order_repo import OrderRepo
from app.routers.issue38_payment_validation_router import create_order_repo

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


def test_valid_payment_returns_200(tmp_path):
    """Valid card details return 200."""
    _override(tmp_path)
    r = client.post("/payments/validate", json=VALID_PAYLOAD)
    assert r.status_code == 200


def test_valid_payment_status_is_accepted(tmp_path):
    """Valid card details produce payment_status 'accepted'."""
    _override(tmp_path)
    r = client.post("/payments/validate", json=VALID_PAYLOAD)
    assert r.json()["payment_status"] == "accepted"


def test_valid_payment_order_status_is_paid(tmp_path):
    """Valid card details produce order_status 'paid'."""
    _override(tmp_path)
    r = client.post("/payments/validate", json=VALID_PAYLOAD)
    assert r.json()["order_status"] == "paid"


def test_valid_payment_rejection_reason_is_empty(tmp_path):
    """Accepted payment has an empty rejection_reason."""
    _override(tmp_path)
    r = client.post("/payments/validate", json=VALID_PAYLOAD)
    assert r.json()["rejection_reason"] == ""


def test_short_card_number_is_rejected(tmp_path):
    """Card number shorter than 16 digits is rejected."""
    _override(tmp_path)
    r = client.post("/payments/validate", json={**VALID_PAYLOAD, "card_number": "12345"})
    assert r.json()["payment_status"] == "rejected"
    assert r.json()["order_status"] == "payment_failed"


def test_short_cvv_is_rejected(tmp_path):
    """CVV shorter than 3 digits is rejected."""
    _override(tmp_path)
    r = client.post("/payments/validate", json={**VALID_PAYLOAD, "cvv": "12"})
    assert r.json()["payment_status"] == "rejected"


def test_expired_card_is_rejected(tmp_path):
    """Expired card is rejected."""
    _override(tmp_path)
    payload = {**VALID_PAYLOAD, "expiry_year": datetime.now().year - 1, "expiry_month": 1}
    r = client.post("/payments/validate", json=payload)
    assert r.json()["payment_status"] == "rejected"


def test_rejected_payment_has_rejection_reason(tmp_path):
    """Rejected payment includes a non-empty rejection_reason."""
    _override(tmp_path)
    r = client.post("/payments/validate", json={**VALID_PAYLOAD, "cvv": "12"})
    assert r.json()["rejection_reason"] != ""


def test_order_not_found_returns_404(tmp_path):
    """Unknown order returns 404."""
    _override(tmp_path, orders=[])
    r = client.post("/payments/validate", json=VALID_PAYLOAD)
    assert r.status_code == 404


def test_response_schema_has_all_fields(tmp_path):
    """Response contains all required fields."""
    _override(tmp_path)
    r = client.post("/payments/validate", json=VALID_PAYLOAD)
    for field in ("order_id", "payment_status", "order_status", "rejection_reason"):
        assert field in r.json()
      
