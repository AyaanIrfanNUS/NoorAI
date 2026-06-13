"""
User schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    location_lat: float | None = None
    location_lng: float | None = None
    currency: str = "USD"


class UserUpdate(BaseModel):
    full_name: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    currency: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    location_lat: float | None
    location_lng: float | None
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime