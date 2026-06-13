"""
Zakat calculation schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ZakatInput(BaseModel):
    cash_savings: float = 0
    gold_value: float = 0
    silver_value: float = 0
    business_assets: float = 0


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