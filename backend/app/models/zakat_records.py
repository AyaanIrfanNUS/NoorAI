"""
Zakat record model.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ZakatRecord(Base):
    __tablename__ = "zakat_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    gold_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    silver_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    cash_savings: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    business_assets: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    nisab_threshold: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    zakat_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="zakat_records")