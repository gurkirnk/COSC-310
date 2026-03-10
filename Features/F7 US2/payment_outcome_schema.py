"""Pydantic schemas for Payment outcome notification.

F7 US2: As a customer, I want to know whether my payment was accepted or rejected
     so that I know if my order was successful.
"""

from pydantic import BaseModel


class PaymentOutcomeRequest(BaseModel):
    """Payload to submit a payment and receive an outcome notification."""
    order_id: str
    customer_id: str
    card_number: str
    cvv: str
    expiry_month: int
    expiry_year: int


class PaymentOutcomeResponse(BaseModel):
    """Clear success or failure response shown to the customer."""
    order_id: str
    payment_status: str   # "accepted" or "rejected"
    order_status: str     # "paid" or "payment_failed"
    message: str          # Human-readable outcome message shown to the customer
