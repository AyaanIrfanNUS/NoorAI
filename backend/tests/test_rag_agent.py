"""
Unit tests for RAG agent logic that doesn't require mocking external calls.
"""

from app.ai.agents.rag_agent import _needs_web_search
from unittest.mock import patch
from app.ai.agents.rag_agent import ask, _needs_web_search
from tests.helpers.cerebras_mocks import make_tool_call, make_tool_call_response, make_text_response


def test_needs_web_search_empty_chunks():
    # No chunks at all means nothing was retrieved, so a web search is needed.
    assert _needs_web_search([]) is True


def test_needs_web_search_low_similarity():
    chunks = [{"similarity": 0.3}, {"similarity": 0.4}]
    assert _needs_web_search(chunks) is True


def test_needs_web_search_high_similarity():
    chunks = [{"similarity": 0.7}, {"similarity": 0.6}]
    assert _needs_web_search(chunks) is False


def test_needs_web_search_exact_lookup_chunks():
    # Chunks with no similarity score (e.g. exact surah/dua lookups) are
    # treated as sufficient on their own, without triggering a web search.
    chunks = [{"similarity": None}, {"similarity": None}]
    assert _needs_web_search(chunks) is False


def test_needs_web_search_mixed_chunks_uses_best_score():
    # One strong match among weaker ones is enough to skip the web search.
    chunks = [{"similarity": 0.2}, {"similarity": 0.65}]
    assert _needs_web_search(chunks) is False


def test_ask_returns_answer_from_duas(db_session):
    # Simulates the model selecting search_duas in Call 1, then writing a
    # final answer in Call 2, verifying the two-call flow end to end.
    with patch("app.ai.agents.rag_agent.CEREBRAS_CLIENT") as mock_client:
        mock_client.chat.completions.create.side_effect = [
            make_tool_call_response(
                [make_tool_call("search_duas", {"situation": "anxiety"})]
            ),
            make_text_response("Here is a dua for anxiety: ..."),
        ]

        result = ask("What is the dua for anxiety?")

    assert result["answer"] == "Here is a dua for anxiety: ..."
    assert "search_duas" in result["tools_used"]


def test_ask_skips_retrieval_on_no_retrieval_needed(db_session):
    # Simulates the model choosing no_retrieval_needed for a pure follow-up;
    # Call 2 should still run and produce an answer from history alone.
    with patch("app.ai.agents.rag_agent.CEREBRAS_CLIENT") as mock_client:
        mock_client.chat.completions.create.side_effect = [
            make_tool_call_response(
                [make_tool_call("no_retrieval_needed", {})]
            ),
            make_text_response("Here's the shorter version: ..."),
        ]

        history = [
            {"role": "user", "content": "What is the dua for anxiety?"},
            {"role": "assistant", "content": "The dua is: ..."},
        ]
        result = ask("Can you shorten that?", history=history)

    assert result["answer"] == "Here's the shorter version: ..."
    assert result["tools_used"] == []
    assert result["sources"] == []


def test_ask_returns_fallback_message_with_no_history_and_no_chunks(db_session):
    # A first-turn question with no matching tools called and nothing found
    # should return the standard fallback, without attempting Call 2.
    with patch("app.ai.agents.rag_agent.CEREBRAS_CLIENT") as mock_client:
        mock_client.chat.completions.create.side_effect = [
            make_tool_call_response(
                [make_tool_call("no_retrieval_needed", {})]
            ),
        ]

        result = ask("asdkjaslkdj random gibberish")

    assert result["answer"] == "I wasn't able to find relevant information for that question."
    assert result["sources"] == []