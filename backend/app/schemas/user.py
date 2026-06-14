"""
User schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

VALID_MADHABS = {"hanafi", "shafi", "maliki", "hanbali", "jafari"}


class UserCreate(BaseModel):
    """Payload for new user registration.

    Email is normalized to lowercase with surrounding whitespace
    stripped, to prevent duplicate accounts differing only by case
    or formatting. Password must be at least 8 characters.

    calculation_method is intentionally not accepted here - it is
    derived server-side from location_country at registration time.
    """

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    location_lat: float | None = None
    location_lng: float | None = None
    location_country: str | None = None
    currency: str = "USD"
    madhab: str = "shafi"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("location_country")
    @classmethod
    def validate_location_country(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        if len(v) != 2 or not v.isalpha():
            raise ValueError("location_country must be a 2-letter ISO country code")
        return v

    @field_validator("madhab")
    @classmethod
    def validate_madhab(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_MADHABS:
            raise ValueError(f"madhab must be one of {sorted(VALID_MADHABS)}")
        return v


class UserUpdate(BaseModel):
    """Profile update payload.

    calculation_method is not included - it is system-managed and not
    user-editable.
    """

    full_name: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    location_country: str | None = None
    currency: str | None = None
    madhab: str | None = None

    @field_validator("location_country")
    @classmethod
    def validate_location_country(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        if len(v) != 2 or not v.isalpha():
            raise ValueError("location_country must be a 2-letter ISO country code")
        return v

    @field_validator("madhab")
    @classmethod
    def validate_madhab(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if v not in VALID_MADHABS:
            raise ValueError(f"madhab must be one of {sorted(VALID_MADHABS)}")
        return v


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    location_lat: float | None
    location_lng: float | None
    location_country: str | None
    currency: str
    calculation_method: int
    madhab: str
    is_active: bool
    created_at: datetime
    updated_at: datetime