"""
Tool: search_quran_by_surah
Direct lookup of a Quran surah's chunks by name, bypassing semantic search.
Used when a question names a specific surah — semantic search alone is
unreliable for exact reference lookups (e.g. "Al-Inshirah" vs stored "Ash-Sharh").
"""

from app.data.islamic_mappings import SURAH_NAMES, SURAH_ALIASES


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_quran_by_surah",
        "description": (
            "Look up the full text of a specific named Quran surah (chapter). "
            "Use this when the user asks about a surah by name or number, "
            "e.g. 'What does Surah Al-Inshirah say?' or 'Tell me about Surah 94'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "surah_query": {
                    "type": "string",
                    "description": "The surah name or number as mentioned by the user, e.g. 'Al-Inshirah' or '94'.",
                }
            },
            "required": ["surah_query"],
        },
    },
}


def find_surah_number(query: str) -> int | None:
    """Match a surah name/alias/number mentioned in text to its surah number."""
    query_lower = query.lower().strip()

    if query_lower.isdigit():
        num = int(query_lower)
        if 1 <= num <= 114:
            return num

    for alias, num in SURAH_ALIASES.items():
        if alias in query_lower:
            return num

    for num, name in SURAH_NAMES.items():
        if name.lower() in query_lower:
            return num

    return None


def search_quran_by_surah(surah_query: str, conn) -> list[dict]:
    """Fetch all chunks for a given surah, ordered by ayah position."""
    surah_number = find_surah_number(surah_query)
    if surah_number is None:
        return []

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_file, content, chunk_metadata
            FROM document_chunks
            WHERE chunk_metadata->>'source_type' = 'quran'
              AND (chunk_metadata->>'surah_number')::int = %s
            ORDER BY (chunk_metadata->>'ayah_start')::int
            """,
            (surah_number,),
        )
        rows = cur.fetchall()

    return [{"source_file": r[0], "content": r[1], "metadata": r[2]} for r in rows]