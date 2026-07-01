"""
Tool: search_knowledge_base
General semantic search across all ingested Islamic knowledge sources.
Used for open-ended questions about seerah, fiqh, prophet stories,
general Quran themes — anything not requiring a specific surah or dua lookup.
"""

from app.data.islamic_mappings import TOC_PATTERNS

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_knowledge_base",
        "description": (
            "Search the Islamic knowledge base for information relevant to a question. "
            "Use this for open-ended questions about Islamic history, fiqh, seerah, "
            "prophet stories, or general Quranic themes where no specific surah or dua "
            "is being requested. e.g. 'What does Islam say about patience?', "
            "'Tell me about the story of Prophet Musa', 'How do I perform wudu?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query derived from the user's question.",
                }
            },
            "required": ["query"],
        },
    },
}

RETRIEVAL_K = 5
NEIGHBOR_WINDOW = 1

TOC_PATTERNS = [
    "contents", "table of contents", "chapter 1", "1. prophet", "1. introduction"
]


def _is_toc_chunk(content: str) -> bool:
    """Detect table of contents chunks that have no real narrative value."""
    first_100 = content.lower()[:100]
    return any(pattern in first_100 for pattern in TOC_PATTERNS)


def search_knowledge_base(query: str, conn, embedder) -> list[dict]:
    """
    Semantic search across all document_chunks, expanded with neighboring
    chunks from the same source for fuller context. TOC chunks are filtered out.
    """
    query_embedding = embedder.encode(query, normalize_embeddings=True).tolist()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_file, content, chunk_index, chunk_metadata,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM document_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, RETRIEVAL_K),
        )
        top_matches = cur.fetchall()

    expanded = []
    seen_keys = set()

    for source_file, content, chunk_index, metadata, similarity in top_matches:
        key = (source_file, chunk_index)
        if key in seen_keys:
            continue
        if _is_toc_chunk(content):
            continue
        seen_keys.add(key)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT content FROM document_chunks
                WHERE source_file = %s AND chunk_index BETWEEN %s AND %s
                ORDER BY chunk_index
                """,
                (source_file, chunk_index - NEIGHBOR_WINDOW, chunk_index + NEIGHBOR_WINDOW),
            )
            neighbors = cur.fetchall()

        combined_content = " ".join(n[0] for n in neighbors)
        expanded.append({
            "source_file": source_file,
            "content": combined_content,
            "metadata": metadata,
            "similarity": similarity,
        })

    return expanded