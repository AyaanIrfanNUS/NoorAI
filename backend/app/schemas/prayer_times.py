"""
Prayer times schemas.
"""

from pydantic import BaseModel


class PrayerTimesResponse(BaseModel):
    date: str
    timezone: str
    timings: dict[str, str]


class NextPrayerResponse(BaseModel):
    prayer_name: str
    time: str
    timezone: str
    seconds_until: int