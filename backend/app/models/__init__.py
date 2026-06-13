"""
Model imports.

Importing all models here ensures they are registered with SQLAlchemy's
metadata before Alembic generates migrations.
"""

from app.models.users import User
from app.models.prayer_logs import PrayerLog
from app.models.zakat_records import ZakatRecord
from app.models.chat_sessions import ChatSession
from app.models.chat_messages import ChatMessage
from app.models.document_chunks import DocumentChunk

__all__ = [
    "User",
    "PrayerLog",
    "ZakatRecord",
    "ChatSession",
    "ChatMessage",
    "DocumentChunk",
]