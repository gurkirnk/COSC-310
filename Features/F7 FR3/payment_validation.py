"""Pydantic schemas for Payment validation.
The system shall determine whether a payment is accepted or rejected
     based on pre-defined rules.
"""

from pydantic import BaseModel


class PaymentValidationRequest(BaseModel):
    """Payload submitted for payment validation."""
    order_id: str
    customer_id: str
    card_number: str   # Must be exactly 16 numeric digits
    cvv: str           # Must be exactly 3 numeric digits
    expiry_month: int  # Must be 1–12
    expiry_year: int   # Must not be in the past


class PaymentValidationResponse(BaseModel):
    """Outcome of a payment validation attempt."""
    order_id: str
    payment_status: str   # "accepted" or "rejected"
    order_status: str     # "paid" or "payment_failed"
    rejection_reason: str  # Empty string when accepted
