"""
User schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    """Payload for new user registration.

    Email is normalized to lowercase with surrounding whitespace
    stripped, to prevent duplicate accounts differing only by case
    or formatting. Password must be at least 8 characters.
    """

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    location_lat: float | None = None
    location_lng: float | None = None
    currency: str = "USD"
    calculation_method: int = 3

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserUpdate(BaseModel):
    full_name: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    currency: str | None = None
    calculation_method: int | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    location_lat: float | None
    location_lng: float | None
    currency: str
    calculation_method: int
    is_active: bool
    created_at: datetime
    updated_at: datetime