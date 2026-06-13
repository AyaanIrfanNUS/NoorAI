"""
Zakat calculator endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.zakat import calculate_zakat
from app.models.users import User
from app.models.zakat_records import ZakatRecord
from app.schemas.common import PaginatedResponse
from app.schemas.zakat import ZakatInput, ZakatRecordRead, ZakatResult

router = APIRouter(prefix="/zakat", tags=["zakat"])


@router.post("/calculate", response_model=ZakatResult, status_code=status.HTTP_201_CREATED)
async def calculate(
    payload: ZakatInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    breakdown = await calculate_zakat(
        cash_savings=payload.cash_savings,
        gold_value=payload.gold_value,
        silver_value=payload.silver_value,
        business_assets=payload.business_assets,
        currency=current_user.currency,
    )

    record = ZakatRecord(
        user_id=current_user.id,
        cash_savings=payload.cash_savings,
        gold_value=payload.gold_value,
        silver_value=payload.silver_value,
        business_assets=payload.business_assets,
        nisab_threshold=breakdown["nisab_threshold"],
        zakat_amount=breakdown["zakat_amount"],
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return ZakatResult(
        id=record.id,
        total_wealth=breakdown["total_wealth"],
        nisab_threshold=breakdown["nisab_threshold"],
        nisab_gold=breakdown["nisab_gold"],
        nisab_silver=breakdown["nisab_silver"],
        is_zakat_due=breakdown["is_zakat_due"],
        zakat_amount=breakdown["zakat_amount"],
        currency=breakdown["currency"],
        calculated_at=record.calculated_at,
    )


@router.get("/history", response_model=PaginatedResponse[ZakatRecordRead])
async def get_history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    count_result = await db.execute(
        select(func.count(ZakatRecord.id)).where(ZakatRecord.user_id == current_user.id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(ZakatRecord)
        .where(ZakatRecord.user_id == current_user.id)
        .order_by(ZakatRecord.calculated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = result.scalars().all()

    return PaginatedResponse[ZakatRecordRead](
        items=[ZakatRecordRead.model_validate(r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
    )