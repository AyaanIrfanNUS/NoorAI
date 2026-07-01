"""
Chat endpoints backed by the RAG agent.
"""

import uuid

import json
from fastapi.responses import StreamingResponse
from app.ai.agents.rag_agent import ask_stream
from app.core.ai_response_streaming import async_generator_from_sync

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.ai.agents.rag_agent import ask
from app.core.database import get_db
from app.core.deps import get_current_user, optional_current_user
from app.core.limiter import limiter
from app.models.chat_messages import ChatMessage
from app.models.chat_sessions import ChatSession
from app.models.users import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatResponse,
    ChatSessionListItem,
)

router = APIRouter(prefix="/chat", tags=["chat"])

# Session titles are derived from the first question rather than
# LLM-generated, keeping session creation fast and free of extra API cost.
SESSION_TITLE_MAX_LENGTH = 50

# Number of prior messages included as conversation context in each request.
HISTORY_WINDOW = 10


@router.post("/message", response_model=ChatResponse)
@limiter.limit("10/minute")
async def send_message(
    request: Request,
    payload: ChatMessageCreate,
    current_user: User | None = Depends(optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Anonymous users get a direct answer with no persistence: no session,
    # no message history, and any session_id they send is ignored.
    if current_user is None:
        result = await run_in_threadpool(ask, payload.question, None, None)
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            tools_used=result["tools_used"],
            session_id=None,
        )

    # Reuse the session if a valid, owned session_id was provided;
    # otherwise start a new one.
    session = None
    if payload.session_id is not None:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == payload.session_id,
                ChatSession.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()

    if session is None:
        session = ChatSession(
            user_id=current_user.id,
            title=payload.question[:SESSION_TITLE_MAX_LENGTH],
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # Persist the user's question before calling the agent, so it is not
    # lost if the agent call fails.
    user_message = ChatMessage(session_id=session.id, role="user", content=payload.question)
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    # Load the most recent prior messages (excluding the one just saved)
    # as conversation context, oldest first.
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id, ChatMessage.id != user_message.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(HISTORY_WINDOW)
    )
    history_messages = list(reversed(history_result.scalars().all()))
    history = [{"role": m.role, "content": m.content} for m in history_messages]

    user_context = {
        "name": current_user.full_name,
        "madhab": current_user.madhab,
        "location_country": current_user.location_country,
    }

    # ask() is synchronous (blocking DB/LLM calls); running it in a thread
    # pool keeps the event loop free to serve other requests concurrently.
    result = await run_in_threadpool(ask, payload.question, user_context, history)

    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result["answer"],
        sources=result["sources"],
    )
    db.add(assistant_message)
    await db.execute(
        update(ChatSession).where(ChatSession.id == session.id).values(updated_at=func.now())
    )
    await db.commit()

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        tools_used=result["tools_used"],
        session_id=session.id,
    )


@router.post("/message/stream")
@limiter.limit("10/minute")
async def send_message_stream(
    request: Request,
    payload: ChatMessageCreate,
    current_user: User | None = Depends(optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Session and history are prepared up front, before any streaming starts,
    # using the same session reuse/creation logic as the non-streaming endpoint.
    session = None
    user_context = None
    history = None

    if current_user is not None:
        if payload.session_id is not None:
            result = await db.execute(
                select(ChatSession).where(
                    ChatSession.id == payload.session_id,
                    ChatSession.user_id == current_user.id,
                )
            )
            session = result.scalar_one_or_none()

        if session is None:
            session = ChatSession(
                user_id=current_user.id,
                title=payload.question[:SESSION_TITLE_MAX_LENGTH],
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)

        # The user's question is saved before generation begins, so it is
        # not lost if the agent call fails partway through.
        user_message = ChatMessage(session_id=session.id, role="user", content=payload.question)
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)

        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id, ChatMessage.id != user_message.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(HISTORY_WINDOW)
        )
        history_messages = list(reversed(history_result.scalars().all()))
        history = [{"role": m.role, "content": m.content} for m in history_messages]

        user_context = {
            "name": current_user.full_name,
            "madhab": current_user.madhab,
            "location_country": current_user.location_country,
        }

    async def event_generator():
        # Tokens are relayed to the client as they arrive and simultaneously
        # accumulated here, since the full answer is only persisted once
        # streaming completes, not written token by token.
        full_answer = ""
        final_sources = []
        final_tools_used = []

        try:
            async for chunk in async_generator_from_sync(ask_stream, payload.question, user_context, history):
                if chunk["type"] == "token":
                    full_answer += chunk["content"]
                    yield f"data: {json.dumps({'token': chunk['content']})}\n\n"
                elif chunk["type"] == "done":
                    final_sources = chunk["sources"]
                    final_tools_used = chunk["tools_used"]
        except Exception:
            # A partial answer is not persisted; the client is told the
            # stream failed so it can retry rather than treat a cut-off
            # answer as complete.
            error_payload = {"error": "The assistant is temporarily unavailable. Please try again."}
            yield f"data: {json.dumps(error_payload)}\n\n"
            return

        if current_user is not None and session is not None:
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=full_answer,
                sources=final_sources,
            )
            db.add(assistant_message)
            await db.execute(
                update(ChatSession).where(ChatSession.id == session.id).values(updated_at=func.now())
            )
            await db.commit()

        # Sent last so the client can distinguish "still streaming" from
        # "response complete", along with metadata not known until the
        # full answer has been generated.
        done_payload = {
            "done": True,
            "sources": final_sources,
            "tools_used": final_tools_used,
            "session_id": str(session.id) if session else None,
        }
        yield f"data: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/sessions", response_model=list[ChatSessionListItem])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    # message_count and last_message_preview are derived per session rather
    # than stored, since sessions are updated infrequently relative to reads.
    items = []
    for session in sessions:
        count_result = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
        )
        message_count = count_result.scalar_one()

        last_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        last_message = last_result.scalar_one_or_none()

        items.append(
            ChatSessionListItem(
                id=session.id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=message_count,
                last_message_preview=last_message.content[:100] if last_message else None,
            )
        )

    return items


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageRead])
async def get_session_messages(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == current_user.id
        )
    )
    if session_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = messages_result.scalars().all()

    return [ChatMessageRead.model_validate(m) for m in messages]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == current_user.id
        )
    )
    session = session_result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    # Hard delete: chat history carries no audit/recovery requirement,
    # unlike user accounts. Messages are removed before the session since
    # the foreign key is not set up to cascade at the database level.
    await db.execute(ChatMessage.__table__.delete().where(ChatMessage.session_id == session_id))
    await db.execute(ChatSession.__table__.delete().where(ChatSession.id == session_id))
    await db.commit()