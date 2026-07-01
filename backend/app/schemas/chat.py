"""
Chat schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatMessageCreate(BaseModel):
    question: str
    session_id: uuid.UUID | None = None


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    sources: list | None
    created_at: datetime


class ChatResponse(BaseModel):
    """
    Shape returned by POST /chat/message for both anonymous and 
    authenticated users; session_id is None for anonymous requests.
    """
    answer: str
    sources: list[dict]
    tools_used: list[str]
    session_id: uuid.UUID | None = None


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatSessionListItem(BaseModel):
    """
    Summary shape for GET /chat/sessions, includes derived 
    fields not present on the ChatSession model itself.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_preview: str | None = None