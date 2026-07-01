"""
Tool: search_web
Live web search via Tavily, used as a fallback when our curated knowledge base
does not have strong matches for the user's question (see _needs_web_search in
rag_agent.py). Results are NOT scholar-verified — must be cited distinctly from
Quran/dua/knowledge-base sources in the system prompt.
"""

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": (
            "Search the live web for current information not found in the curated "
            "Islamic knowledge base — e.g. local services, current dates/events, "
            "or topics outside the knowledge base's scope."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to run against the web.",
                }
            },
            "required": ["query"],
        },
    },
}

RETRIEVAL_K = 3


def search_web(query: str, tavily_client, location: str | None = None) -> list[dict]:
    """
    Runs a live Tavily web search and returns results shaped like our other
    tool outputs. If `location` is provided (e.g. user's location_country),
    it's appended to the query to bias results geographically — Tavily has
    no native geo parameter, so this is done via query text.
    """
    search_query = f"{query} in {location}" if location else query
    response = tavily_client.search(query=search_query, max_results=RETRIEVAL_K)
    results = response.get("results", [])

    return [
        {
            "source_file": r.get("url", "unknown"),
            "content": f"{r.get('title', '')}\n{r.get('content', '')}".strip(),
            "metadata": {
                "source_type": "web",
                "url": r.get("url"),
                "title": r.get("title"),
            },
            "similarity": None,
        }
        for r in results
    ]