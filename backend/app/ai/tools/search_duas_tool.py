"""
Tool: search_duas
Filtered semantic search restricted to dua entries only.
Used when the user is specifically asking for a dua/supplication for a situation.
Returns scholar-verified duas from the curated structured collection.
"""

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_duas",
        "description": (
            "Search for Islamic duas (supplications) relevant to a specific situation. "
            "Use this when the user asks for a dua or supplication for something, "
            "e.g. 'What is the dua for anxiety?', 'Give me a dua before eating', "
            "'What should I recite when travelling?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "situation": {
                    "type": "string",
                    "description": "The situation or need the user wants a dua for, e.g. 'anxiety', 'before eating', 'travelling'.",
                }
            },
            "required": ["situation"],
        },
    },
}

RETRIEVAL_K = 3


def search_duas(situation: str, conn, embedder) -> list[dict]:
    """
    Semantic search restricted to source_type='dua' chunks only.
    Returns the top matching duas for the given situation.
    """
    query_embedding = embedder.encode(situation, normalize_embeddings=True).tolist()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_file, content, chunk_metadata,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM document_chunks
            WHERE chunk_metadata->>'source_type' = 'dua'
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, RETRIEVAL_K),
        )
        rows = cur.fetchall()

    return [
        {
            "source_file": r[0],
            "content": r[1],
            "metadata": r[2],
            "similarity": r[3],
        }
        for r in rows
    ]