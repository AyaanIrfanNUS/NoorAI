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
from app.data.islamic_mappings import DUA_KEYWORDS, PROPHET_SURAH_MAP, STORY_KEYWORDS

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

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL")

# ── Shared clients ────────────────────────────────────────────────────────────
EMBEDDER = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
CEREBRAS_CLIENT = Cerebras(api_key=CEREBRAS_API_KEY)

# ── Prompt ────────────────────────────────────────────────────────────────────
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "chat_system.txt"
SYSTEM_PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")
MAX_TOKENS = 5000

# ── Tool registry ─────────────────────────────────────────────────────────────
TOOLS = [QURAN_SCHEMA, KB_SCHEMA, DUAS_SCHEMA]

TOOL_FUNCTIONS = {
    "search_quran_by_surah": lambda args, conn: search_quran_by_surah(args["surah_query"], conn),
    "search_knowledge_base": lambda args, conn: search_knowledge_base(args["query"], conn, EMBEDDER),
    "search_duas": lambda args, conn: search_duas(args["situation"], conn, EMBEDDER),
}


def _get_connection():
    url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )
    return psycopg2.connect(url)


def build_context_string(chunks: list[dict]) -> str:
    parts = [f"[Source {i}: {c['source_file']}]\n{c['content']}" for i, c in enumerate(chunks, 1)]
    return "\n\n".join(parts)


def ask(question: str) -> dict:
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
        response = CEREBRAS_CLIENT.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an Islamic knowledge assistant. "
                        "Use the most relevant tool(s) to find information. "
                        "You may call multiple tools if the question spans multiple topics."
                    ),
                },
                {"role": "user", "content": question},
            ],
            tools=TOOLS,
            tool_choice="required",
            max_tokens=500,
        )

        choice = response.choices[0].message
        tool_results_for_messages = []

        for tool_call in choice.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            if tool_name in tools_used:
                # Already ran this tool — skip but still add to message history
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

        if not all_chunks:
            return {
                "answer": "I wasn't able to find relevant information for that question.",
                "sources": [],
                "tools_used": tools_used,
            }

        # ── Call 2: LLM writes final answer ───────────────────────────────────
        combined_context = build_context_string(all_chunks)
        prompt = SYSTEM_PROMPT_TEMPLATE.format(context=combined_context, question=question)

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
        sources = [
            {
                "source_file": c["source_file"],
                "similarity": round(c["similarity"], 3) if c.get("similarity") else "direct_lookup"
            }
            for c in all_chunks
        ]

        return {"answer": answer, "sources": sources, "tools_used": tools_used}

    finally:
        conn.close()


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