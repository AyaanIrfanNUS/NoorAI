"""
User model.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", server_default="USD", nullable=False)
    calculation_method: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    madhab: Mapped[str] = mapped_column(String(10), default="shafi", server_default="shafi", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    prayer_logs: Mapped[list["PrayerLog"]] = relationship(back_populates="user")
    zakat_records: Mapped[list["ZakatRecord"]] = relationship(back_populates="user")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user")