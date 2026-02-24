"""Pydantic schemas for authentication models"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login request payload - accepts email or phone_number plus password."""
    identifier: str  # email or phone number
    password: str


class TokenResponse(BaseModel):
    """Response returned after successful login."""
    user_id: str
    name: str
    role: str
    message: str
