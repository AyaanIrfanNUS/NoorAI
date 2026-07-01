"""
NoorAI RAG Agent
Orchestrates tool-calling loop: LLM decides which retrieval tool to use,
we execute it, then LLM writes the final grounded answer.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from cerebras.cloud.sdk import Cerebras
import psycopg2
from psycopg2 import pool as psycopg2_pool
from app.data.islamic_mappings import DUA_KEYWORDS, PROPHET_SURAH_MAP, STORY_KEYWORDS
from tavily import TavilyClient
from app.ai.tools.search_web_tool import search_web

from app.ai.tools.search_quran_by_surah_tool import (
    search_quran_by_surah,
    TOOL_SCHEMA as QURAN_SCHEMA,
)
from app.ai.tools.search_knowledge_base_tool import (
    search_knowledge_base,
    TOOL_SCHEMA as KB_SCHEMA,
)
from app.ai.tools.search_duas_tool import (
    search_duas,
    TOOL_SCHEMA as DUAS_SCHEMA,
)
from app.ai.tools.no_retrieval_tool import TOOL_SCHEMA as NO_RETRIEVAL_SCHEMA

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ── Shared clients ────────────────────────────────────────────────────────────
EMBEDDER = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
CEREBRAS_CLIENT = Cerebras(api_key=CEREBRAS_API_KEY)
TAVILY_CLIENT = TavilyClient(api_key=TAVILY_API_KEY)

# ── Prompt ────────────────────────────────────────────────────────────────────
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "chat_system.txt"
SYSTEM_PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")

# ── Tool registry ─────────────────────────────────────────────────────────────
TOOLS = [QURAN_SCHEMA, KB_SCHEMA, DUAS_SCHEMA, NO_RETRIEVAL_SCHEMA]

TOOL_FUNCTIONS = {
    "search_quran_by_surah": lambda args, conn: search_quran_by_surah(args["surah_query"], conn),
    "search_knowledge_base": lambda args, conn: search_knowledge_base(args["query"], conn, EMBEDDER),
    "search_duas": lambda args, conn: search_duas(args["situation"], conn, EMBEDDER),
}

# ── Response Thresholds ─────────────────────────────────────────────────────────────
MAX_TOKENS = 5000 # holds the maximum tokens allowed in the output response
SIMILARITY_THRESHOLD = 0.5 # holds the similarity threshold before any web search go through tavily

# ── Connection Thresholds ─────────────────────────────────────────────────────────────
MIN_CONN = 2
MAX_CONN = 10


_DB_URL_NORMALIZED = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace(
    "postgresql+psycopg2://", "postgresql://"
)

# Connection pool shared across concurrent requests; maxconn bounds usage against the database's connection limit.
CONNECTION_POOL = psycopg2_pool.ThreadedConnectionPool(
    minconn=MIN_CONN,
    maxconn=MAX_CONN,
    dsn=_DB_URL_NORMALIZED,
)


def _get_connection():
    return CONNECTION_POOL.getconn()

def _release_connection(conn):
    CONNECTION_POOL.putconn(conn)



def build_context_string(chunks: list[dict]) -> str:
    parts = [f"[Source {i}: {c['source_file']}]\n{c['content']}" for i, c in enumerate(chunks, 1)]
    return "\n\n".join(parts)


def ask(question: str, user: dict | None = None, history: list[dict] | None = None) -> dict:
    conn = _get_connection()

    try:
        # ── Pre-run mandatory tools ───────────────────────────────────────────
        all_chunks = []
        tools_used = []

        for tool_spec in _mandatory_tools(question):
            if ":" in tool_spec:
                tool_name, tool_arg = tool_spec.split(":", 1)
            else:
                tool_name, tool_arg = tool_spec, None

            tool_fn = TOOL_FUNCTIONS.get(tool_name)
            if not tool_fn:
                continue

            if tool_name == "search_quran_by_surah":
                chunks = tool_fn({"surah_query": tool_arg}, conn)
            elif tool_name == "search_knowledge_base":
                chunks = tool_fn({"query": question}, conn)
            elif tool_name == "search_duas":
                chunks = tool_fn({"situation": question}, conn)
            else:
                chunks = []

            if chunks:
                all_chunks.extend(chunks)
                if tool_name not in tools_used:
                    tools_used.append(tool_name)

        # ── Call 1: LLM picks additional tool(s) if needed ───────────────────
        # tool_choice stays required on every turn so retrieval is never
        # silently skipped. History is included so the model can select
        # tools with awareness of what was already discussed.
        response = CEREBRAS_CLIENT.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an Islamic knowledge assistant. "
                        "Use the most relevant tool(s) to find information. "
                        "You may call multiple tools if the question spans multiple topics. "
                        "Call no_retrieval_needed only for pure follow-ups with no new topic — "
                        "for example, after discussing a dua, 'shorten that' needs no_retrieval_needed, "
                        "but 'are there halal restaurants near me' is a new topic and must use a "
                        "retrieval tool, even in the same conversation. "
                        "When calling a retrieval tool, phrase its query as a self-contained "
                        "request, resolving references to earlier context."
                    ),
                },
                *_history_as_messages(history),
                {"role": "user", "content": question},
            ],
            tools=TOOLS,
            tool_choice="required",
            max_tokens=500,
            temperature = 0.1,
        )

        choice = response.choices[0].message
        tool_results_for_messages = []
        # Set when the model explicitly signals no new retrieval is needed,
        # so the web search fallback is not triggered on an empty result set.
        skip_retrieval = False

        for tool_call in (choice.tool_calls or []):
            tool_name = tool_call.function.name

            if tool_name == "no_retrieval_needed":
                skip_retrieval = True
                tool_results_for_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": "Answering from conversation history.",
                })
                continue

            tool_args = json.loads(tool_call.function.arguments)

            if tool_name in tools_used:
                tool_results_for_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": "Already retrieved.",
                })
                continue

            tool_fn = TOOL_FUNCTIONS.get(tool_name)
            if not tool_fn:
                continue

            chunks = tool_fn(tool_args, conn)
            if chunks:
                all_chunks.extend(chunks)
                tools_used.append(tool_name)

            tool_results_for_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": build_context_string(chunks) if chunks else "No results found.",
            })

        if _needs_web_search(all_chunks) and not skip_retrieval:
            location = user.get("location_country") if user else None
            web_chunks = search_web(question, TAVILY_CLIENT, location=location)
            if web_chunks:
                all_chunks.extend(web_chunks)
                tools_used.append("search_web")

        # No chunks and no history means there is genuinely nothing to answer
        # from. If history exists, the model may still be able to answer from
        # conversation context alone, so processing continues to Call 2.
        if not all_chunks and not history:
            return {
                "answer": "I wasn't able to find relevant information for that question.",
                "sources": [],
                "tools_used": tools_used,
            }

        # ── Call 2: LLM writes final answer ───────────────────────────────────
        combined_context = build_context_string(all_chunks)
        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            context=combined_context,
            question=question,
            user_context=_build_user_context(user),
            history=_build_history_string(history),
        )

        messages = [{"role": "user", "content": question}]
        messages.append(choice.model_dump())
        messages.extend(tool_results_for_messages)
        messages.append({"role": "user", "content": prompt})

        final_response = CEREBRAS_CLIENT.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
        )

        answer = final_response.choices[0].message.content
        sources = []
        for c in all_chunks:
            if c.get("similarity") is not None:
                sources.append({"source_file": c["source_file"], "similarity": round(c["similarity"], 3)})
            elif c.get("metadata", {}).get("source_type") == "web":
                sources.append({"source_file": c["source_file"], "similarity": "web_source"})
            else:
                sources.append({"source_file": c["source_file"], "similarity": "direct_lookup"})

        return {"answer": answer, "sources": sources, "tools_used": tools_used}

    finally:
        _release_connection(conn)


# lightweight Python pre-check before Call 1 that forces certain tools to always run together
def _mandatory_tools(question: str) -> list[str]:
    mandatory = []
    q = question.lower()

    if any(w in q for w in DUA_KEYWORDS):
        mandatory.append("search_duas")

    for prophet, surah in PROPHET_SURAH_MAP.items():
        if prophet in q:
            mandatory.append(f"search_quran_by_surah:{surah}")

    if any(w in q for w in STORY_KEYWORDS):
        mandatory.append("search_knowledge_base")

    return mandatory


def _build_user_context(user: dict | None) -> str:
    if not user:
        return "The user is anonymous. Do not assume any personal details about them."

    parts = []
    if user.get("name"):
        parts.append(f"The user's name is {user['name']}.")
    if user.get("madhab"):
        parts.append(f"They follow the {user['madhab']} madhab; consider this for fiqh-related questions.")

    return " ".join(parts) if parts else "The user is authenticated but has no profile details set."


def _build_history_string(history: list[dict] | None) -> str:
    if not history:
        return ""

    lines = ["Previous conversation:"]
    for message in history:
        speaker = "User" if message["role"] == "user" else "NoorAI"
        lines.append(f"{speaker}: {message['content']}")

    return "\n".join(lines)


def _history_as_messages(history: list[dict] | None) -> list[dict]:
    # Formats prior turns as chat messages for the tool-selection call,
    # so the model can recognise follow-up questions that need no new
    # retrieval (e.g. requests to rephrase or shorten a prior answer).
    if not history:
        return []
    return [{"role": m["role"], "content": m["content"]} for m in history]


def _needs_web_search(chunks: list[dict]) -> bool:
    """
    Returns True if retrieved chunks are missing or too weak, meaning
    a live web search should supplement the answer.
    """
    if not chunks:
        return True

    scored = [c["similarity"] for c in chunks if c.get("similarity") is not None]
    if not scored:
        # e.g. only direct_lookup results (surah/dua) — those are exact matches,
        # not similarity-scored, so they don't need web backup
        return False

    return max(scored) < SIMILARITY_THRESHOLD