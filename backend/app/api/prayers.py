"""
Prayer tracker endpoints.
"""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PRAYER_NAMES
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.prayer_logs import PrayerLog
from app.models.users import User
from app.schemas.common import PaginatedResponse
from app.schemas.prayer import (
    PrayerLogCreate,
    PrayerLogRead,
    PrayerStats,
    StreakResponse,
    TodayPrayerStatus,
)

router = APIRouter(prefix="/prayers", tags=["prayers"])


@router.post("/log", response_model=PrayerLogRead, status_code=status.HTTP_201_CREATED)
async def log_prayer(
    payload: PrayerLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.prayer_name not in PRAYER_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"prayer_name must be one of {PRAYER_NAMES}",
        )

    prayer_date = payload.prayed_at.date()

    result = await db.execute(
        select(PrayerLog).where(
            PrayerLog.user_id == current_user.id,
            PrayerLog.prayer_name == payload.prayer_name,
            func.date(PrayerLog.prayed_at) == prayer_date,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{payload.prayer_name} has already been logged for {prayer_date}",
        )

    log = PrayerLog(
        user_id=current_user.id,
        prayer_name=payload.prayer_name,
        prayed_at=payload.prayed_at,
        was_on_time=payload.was_on_time,
        notes=payload.notes,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    return PrayerLogRead.model_validate(log)


@router.get("/today", response_model=list[TodayPrayerStatus])
async def get_today_prayers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = datetime.now(timezone.utc).date()

    result = await db.execute(
        select(PrayerLog).where(
            PrayerLog.user_id == current_user.id,
            func.date(PrayerLog.prayed_at) == today,
        )
    )
    logs = result.scalars().all()
    logs_by_name = {log.prayer_name: log for log in logs}

    return [
        TodayPrayerStatus(
            prayer_name=name,
            completed=name in logs_by_name,
            prayed_at=logs_by_name[name].prayed_at if name in logs_by_name else None,
        )
        for name in PRAYER_NAMES
    ]


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(func.date(PrayerLog.prayed_at), func.count(PrayerLog.id))
        .where(PrayerLog.user_id == current_user.id)
        .group_by(func.date(PrayerLog.prayed_at))
        .order_by(func.date(PrayerLog.prayed_at).desc())
    )
    rows = result.all()

    complete_days = {row[0] for row in rows if row[1] >= len(PRAYER_NAMES)}

    current_streak = 0
    check_date = datetime.now(timezone.utc).date()

    if check_date not in complete_days:
        check_date -= timedelta(days=1)

    while check_date in complete_days:
        current_streak += 1
        check_date -= timedelta(days=1)

    longest_streak = 0
    running_streak = 0
    sorted_days = sorted(complete_days)
    previous_day = None
    for day in sorted_days:
        if previous_day is not None and day == previous_day + timedelta(days=1):
            running_streak += 1
        else:
            running_streak = 1
        longest_streak = max(longest_streak, running_streak)
        previous_day = day

    return StreakResponse(current_streak=current_streak, longest_streak=longest_streak)


@router.get("/history", response_model=PaginatedResponse[PrayerLogRead])
async def get_history(
    page: int = 1,
    page_size: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 30

    count_result = await db.execute(
        select(func.count(PrayerLog.id)).where(PrayerLog.user_id == current_user.id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(PrayerLog)
        .where(PrayerLog.user_id == current_user.id)
        .order_by(PrayerLog.prayed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return PaginatedResponse[PrayerLogRead](
        items=[PrayerLogRead.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=PrayerStats)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(
        select(func.count(PrayerLog.id)).where(PrayerLog.user_id == current_user.id)
    )
    total_prayers_logged = total_result.scalar_one()

    first_log_result = await db.execute(
        select(func.min(PrayerLog.prayed_at)).where(PrayerLog.user_id == current_user.id)
    )
    first_log = first_log_result.scalar_one_or_none()

    if first_log is None:
        completion_rate = 0.0
    else:
        days_tracked = (datetime.now(timezone.utc).date() - first_log.date()).days + 1
        expected_prayers = days_tracked * len(PRAYER_NAMES)
        completion_rate = round((total_prayers_logged / expected_prayers) * 100, 2) if expected_prayers > 0 else 0.0

    streak_result = await db.execute(
        select(func.date(PrayerLog.prayed_at), func.count(PrayerLog.id))
        .where(PrayerLog.user_id == current_user.id)
        .group_by(func.date(PrayerLog.prayed_at))
    )
    rows = streak_result.all()
    complete_days = {row[0] for row in rows if row[1] >= len(PRAYER_NAMES)}

    current_streak = 0
    check_date = datetime.now(timezone.utc).date()

    if check_date not in complete_days:
        check_date -= timedelta(days=1)

    while check_date in complete_days:
        current_streak += 1
        check_date -= timedelta(days=1)

    longest_streak = 0
    running_streak = 0
    previous_day = None
    for day in sorted(complete_days):
        if previous_day is not None and day == previous_day + timedelta(days=1):
            running_streak += 1
        else:
            running_streak = 1
        longest_streak = max(longest_streak, running_streak)
        previous_day = day

    return PrayerStats(
        current_streak=current_streak,
        longest_streak=longest_streak,
        completion_rate=completion_rate,
        total_prayers_logged=total_prayers_logged,
    )