"""
Prayer times endpoints.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.models.users import User
from app.schemas.prayer_times import NextPrayerResponse, PrayerTimesResponse
from app.services.prayer_times import PRAYER_NAMES, PrayerTimesError, get_prayer_times

router = APIRouter(prefix="/prayer-times", tags=["prayer-times"])


def _require_location(current_user: User) -> None:
    """Both endpoints need a saved location - shared check, raised as 400."""
    if current_user.location_lat is None or current_user.location_lng is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location not set. Update your profile with location_lat and location_lng.",
        )


def _school_for_madhab(madhab: str) -> int:
    """Map a user's madhab to Aladhan's school parameter.

    Hanafi uses a later Asr calculation (school=1); all other madhabs
    (Shafi'i, Maliki, Hanbali, Jafari) use the standard convention
    (school=0).
    """
    return 1 if madhab == "hanafi" else 0


@router.get("/today", response_model=PrayerTimesResponse)
async def get_today_prayer_times(
    current_user: User = Depends(get_current_user),
):
    _require_location(current_user)

    try:
        result = await get_prayer_times(
            lat=current_user.location_lat,
            lng=current_user.location_lng,
            calculation_method=current_user.calculation_method,
            school=_school_for_madhab(current_user.madhab),
        )
    except PrayerTimesError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    return PrayerTimesResponse(**result)


@router.get("/next", response_model=NextPrayerResponse)
async def get_next_prayer(
    current_user: User = Depends(get_current_user),
):
    _require_location(current_user)

    try:
        result = await get_prayer_times(
            lat=current_user.location_lat,
            lng=current_user.location_lng,
            calculation_method=current_user.calculation_method,
            school=_school_for_madhab(current_user.madhab),
        )
    except PrayerTimesError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    location_tz = ZoneInfo(result["timezone"])
    now = datetime.now(location_tz)
    today = now.date()

    upcoming = []
    for name in PRAYER_NAMES:
        if name == "Sunrise":
            continue
        hour, minute = map(int, result["timings"][name].split(":"))
        prayer_dt = datetime(today.year, today.month, today.day, hour, minute, tzinfo=location_tz)
        if prayer_dt > now:
            upcoming.append((name, prayer_dt))

    if upcoming:
        next_name, next_dt = upcoming[0]
    else:
        # All of today's prayers have passed - approximate tomorrow's Fajr
        # using today's Fajr time (daily drift is on the order of seconds).
        hour, minute = map(int, result["timings"]["Fajr"].split(":"))
        tomorrow = today + timedelta(days=1)
        next_dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, hour, minute, tzinfo=location_tz)
        next_name = "Fajr"

    seconds_until = int((next_dt - now).total_seconds())

    return NextPrayerResponse(
        prayer_name=next_name,
        time=next_dt.strftime("%H:%M"),
        timezone=result["timezone"],
        seconds_until=max(seconds_until, 0),
    )