from __future__ import annotations

import asyncio
import math
from collections.abc import AsyncIterator, Callable


StreamFactory = Callable[[], AsyncIterator[str]]


async def stream_with_fallback(
    primary: StreamFactory,
    fallback: StreamFactory,
    *,
    chunk_timeout_s: float = 1.0,
) -> AsyncIterator[str]:
    if not math.isfinite(chunk_timeout_s) or chunk_timeout_s <= 0:
        raise ValueError("Invalid timeout")

    for is_primary, provider in ((True, primary), (False, fallback)):
        emitted = False
        iterator = None
        try:
            iterator = aiter(provider())
            while True:
                try:
                    # Time only the provider's next chunk, not the caller's work.
                    async with asyncio.timeout(chunk_timeout_s):
                        chunk = await anext(iterator)
                except StopAsyncIteration:
                    return  # A clean end, even an empty answer, needs no backup.

                emitted = True  # An empty string still counts as a chunk.
                yield chunk
        except Exception:
            if not is_primary or emitted:
                raise
            # Primary failed before output: continue to the backup provider.
            # CancelledError is not an Exception, so cancellation bypasses this.
        finally:
            # Async generators have aclose(); other async iterators may not.
            close = getattr(iterator, "aclose", None)
            if close is not None:
                await close()
