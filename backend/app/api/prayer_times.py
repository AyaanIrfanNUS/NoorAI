"""
Prayer times endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.models.users import User
from app.schemas.prayer_times import PrayerTimesResponse
from app.services.prayer_times import PrayerTimesError, get_prayer_times

router = APIRouter(prefix="/prayer-times", tags=["prayer-times"])


def _require_location(current_user: User) -> None:
    """Both endpoints need a saved location - shared check, raised as 400."""
    if current_user.location_lat is None or current_user.location_lng is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location not set. Update your profile with location_lat and location_lng.",
        )


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
        )
    except PrayerTimesError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    return PrayerTimesResponse(**result)