"""
Tool: no_retrieval_needed
Not a real retrieval tool — an explicit signal the model can choose when a
follow-up question is fully answerable from conversation history alone.
Ensures the tool-selection call always makes an intentional choice, rather
than retrieval being silently skipped or guessed at from an empty result set.
"""

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "no_retrieval_needed",
        "description": (
            "Call this ONLY when the user's message contains no new subject matter "
            "and exclusively references the immediately preceding answer — for "
            "example using words like 'that', 'it', 'shorten', 'simplify', "
            "'rephrase', or 'explain more', with no new noun or topic introduced. "
            "If the message introduces ANY new subject, place, item, or topic not "
            "already present in the conversation history, you must NOT call this — "
            "call a retrieval tool instead, even if the topic seems small or related."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}