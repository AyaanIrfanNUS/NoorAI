"""
Prayer log schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PrayerLogCreate(BaseModel):
    prayer_name: str
    prayed_at: datetime
    was_on_time: bool = True
    notes: str | None = None


class PrayerLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    prayer_name: str
    prayed_at: datetime
    was_on_time: bool
    notes: str | None
    created_at: datetime


class PrayerStats(BaseModel):
    current_streak: int
    longest_streak: int
    completion_rate: float
    total_prayers_logged: int