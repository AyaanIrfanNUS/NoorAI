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
    is_zakat_due: bool
    zakat_amount: float
    calculated_at: datetime