"""
Prayer times service.

Wraps the Aladhan API (https://aladhan.com/prayer-times-api) to fetch
prayer times for a given location, with Redis caching.
"""

import json
from datetime import date, datetime, timezone

import httpx

from app.core.redis import redis_client

ALADHAN_BASE_URL = "https://api.aladhan.com/v1"

PRAYER_NAMES = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

CACHE_TTL_SECONDS = 24 * 60 * 60


class PrayerTimesError(Exception):
    """Raised when prayer times cannot be fetched and no cache exists."""


def _cache_key(lat: float, lng: float, calculation_method: int, target_date: date) -> str:
    """Build a Redis key unique to this location, method, and date."""
    return f"prayer_times:{lat:.4f}:{lng:.4f}:{calculation_method}:{target_date.isoformat()}"


async def _fetch_from_aladhan(lat: float, lng: float, calculation_method: int, target_date: date) -> dict:
    """Call the Aladhan API for a specific date and location."""
    date_str = target_date.strftime("%d-%m-%Y")

    params = {
        "latitude": lat,
        "longitude": lng,
        "method": calculation_method,
    }

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(f"{ALADHAN_BASE_URL}/timings/{date_str}", params=params)
        response.raise_for_status()
        data = response.json()

    if data.get("code") != 200:
        raise PrayerTimesError(f"Aladhan API returned an error: {data}")

    timings = data["data"]["timings"]
    cleaned = {name: timings[name].split(" ")[0] for name in PRAYER_NAMES}

    return {
        "date": target_date.isoformat(),
        "timings": cleaned,
        "timezone": data["data"]["meta"]["timezone"],
    }


async def get_prayer_times(
    lat: float,
    lng: float,
    calculation_method: int,
    target_date: date | None = None,
) -> dict:
    """
    Get prayer times for a location on a given date (defaults to today).

    Checks Redis first. On cache miss, calls Aladhan and caches the result.
    Raises PrayerTimesError if Aladhan is unreachable and nothing is cached.
    """
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    key = _cache_key(lat, lng, calculation_method, target_date)

    cached = await redis_client.get(key)
    if cached:
        return json.loads(cached)

    try:
        result = await _fetch_from_aladhan(lat, lng, calculation_method, target_date)
    except (httpx.HTTPError, PrayerTimesError, KeyError) as exc:
        raise PrayerTimesError(f"Could not fetch prayer times: {exc}") from exc

    await redis_client.set(key, json.dumps(result), ex=CACHE_TTL_SECONDS)
    return result