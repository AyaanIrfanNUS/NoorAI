"""
Direct lookup endpoints for duas and Quran surahs.

Unlike /chat/message, these bypass the RAG agent entirely — no LLM calls,
no tool selection. They return curated content directly and predictably,
for cases where the user already knows what they want rather than asking
an open-ended question.
"""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.ai.agents.rag_agent import EMBEDDER, _get_connection, _release_connection
from app.ai.tools.search_duas_tool import search_duas
from app.ai.tools.search_quran_by_surah_tool import search_quran_by_surah
from app.core.limiter import limiter
from app.data.islamic_mappings import SURAH_NAMES

router = APIRouter(tags=["finder"])


class DuaFindRequest(BaseModel):
    situation: str


class SurahFindRequest(BaseModel):
    name: str


class SurahListItem(BaseModel):
    number: int
    name: str


@router.post("/duas/find")
@limiter.limit("30/minute")
async def find_duas(request: Request, payload: DuaFindRequest):
    conn = _get_connection()
    try:
        chunks = search_duas(payload.situation, conn, EMBEDDER)
    finally:
        _release_connection(conn)

    # Returned exactly as stored: dua content must never be reworded or
    # summarised, so the raw chunk metadata is passed through unmodified.
    return {
        "results": [
            {
                "content": c["content"],
                "metadata": c["metadata"],
                "similarity": round(c["similarity"], 3) if c.get("similarity") is not None else None,
            }
            for c in chunks
        ]
    }


@router.post("/surah/find")
@limiter.limit("30/minute")
async def find_surah(request: Request, payload: SurahFindRequest):
    conn = _get_connection()
    try:
        chunks = search_quran_by_surah(payload.name, conn)
    finally:
        _release_connection(conn)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No surah found matching '{payload.name}'",
        )

    return {
        "results": [
            {
                "content": c["content"],
                "metadata": c["metadata"],
            }
            for c in chunks
        ]
    }


@router.get("/surah/list", response_model=list[SurahListItem])
async def list_surahs():
    # Static 114-entry index; used to power a browsable surah list, e.g.
    # for a full Quran reading page that fetches individual surahs via
    # POST /surah/find once a surah is selected.
    return [SurahListItem(number=num, name=name) for num, name in SURAH_NAMES.items()]