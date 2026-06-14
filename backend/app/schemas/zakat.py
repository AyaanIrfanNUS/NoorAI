"""
Zakat calculation schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ZakatInput(BaseModel):
    """Asset values submitted for a Zakat calculation.

    All fields must be non-negative. The upper bound (1 trillion) is a
    sanity ceiling to reject malformed or absurd input values.
    """

    cash_savings: float = Field(default=0, ge=0, le=1_000_000_000_000)
    gold_value: float = Field(default=0, ge=0, le=1_000_000_000_000)
    silver_value: float = Field(default=0, ge=0, le=1_000_000_000_000)
    business_assets: float = Field(default=0, ge=0, le=1_000_000_000_000)


class ZakatResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    total_wealth: float
    nisab_threshold: float
    nisab_gold: float
    nisab_silver: float
    is_zakat_due: bool
    zakat_amount: float
    currency: str
    calculated_at: datetime


class ZakatRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    cash_savings: float
    gold_value: float
    silver_value: float
    business_assets: float
    nisab_threshold: float
    zakat_amount: float
    calculated_at: datetime