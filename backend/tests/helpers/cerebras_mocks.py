"""
Helpers for building fake Cerebras response objects in tests.

The Cerebras SDK returns nested objects (response.choices[0].message...),
not plain dicts, so tests construct lightweight stand-ins with the same
attribute access pattern rather than mocking the SDK's real classes.
"""

import json
from types import SimpleNamespace


def make_tool_call(tool_name: str, arguments: dict, call_id: str = "call_1"):
    # Mirrors a single entry in response.choices[0].message.tool_calls
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=tool_name, arguments=json.dumps(arguments)),
    )


def make_tool_call_response(tool_calls: list):
    # Mirrors the shape returned by Call 1 when the model selects tool(s).
    message = SimpleNamespace(tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def make_text_response(content: str):
    # Mirrors the shape returned by Call 2 in non-streaming mode.
    message = SimpleNamespace(content=content, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def make_stream_chunks(tokens: list[str]):
    # Mirrors the shape iterated over in ask_stream()'s Call 2 handling:
    # each chunk exposes choices[0].delta.content.
    return [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=token))])
        for token in tokens
    ]