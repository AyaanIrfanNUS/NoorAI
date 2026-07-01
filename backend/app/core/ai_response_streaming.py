"""
Utility for bridging a synchronous generator onto an async consumer.

Cerebras's streaming client is synchronous: iterating it blocks the calling
thread until each chunk arrives. Running that iteration directly inside an
async route would block the event loop for every other request. This helper
runs the synchronous generator on a background thread and relays its items
to an async generator via a thread-safe queue, so the event loop stays free
while tokens are produced.
"""

import queue
import threading
from typing import AsyncGenerator, Generator, TypeVar

T = TypeVar("T")

_SENTINEL = object()


async def async_generator_from_sync(sync_gen_fn, *args, **kwargs) -> AsyncGenerator:
    q: queue.Queue = queue.Queue()

    def _run():
        try:
            for item in sync_gen_fn(*args, **kwargs):
                q.put(item)
        except Exception as exc:
            q.put(exc)
        finally:
            q.put(_SENTINEL)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    loop = __import__("asyncio").get_event_loop()

    while True:
        item = await loop.run_in_executor(None, q.get)
        if item is _SENTINEL:
            break
        if isinstance(item, Exception):
            raise item
        yield item