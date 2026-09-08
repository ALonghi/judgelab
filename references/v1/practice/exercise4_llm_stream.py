from __future__ import annotations
import asyncio
import math
from contextlib import aclosing

from collections.abc import AsyncIterator, Callable


StreamFactory = Callable[[], AsyncIterator[str]]


async def stream_with_fallback(primary: StreamFactory, fallback: StreamFactory, *,
                               chunk_timeout_s: float = 1.0) -> AsyncIterator[str]:
    if not math.isfinite(chunk_timeout_s) or chunk_timeout_s <= 0:
        raise ValueError("Invalid timeout")

    async def timed(factory):
        iterator = factory().__aiter__()
        try:
            while True:
                try:
                    async with asyncio.timeout(chunk_timeout_s):
                        chunk = await anext(iterator)
                except StopAsyncIteration:
                    return
                yield chunk
        finally:
            close = getattr(iterator, "aclose", None)
            if close is not None:
                await close()

    emitted = False
    try:
        async with aclosing(timed(primary)) as iterator:
            async for chunk in iterator:
                emitted = True
                yield chunk
        return
    except Exception:
        if emitted:
            raise
    async with aclosing(timed(fallback)) as iterator:
        async for chunk in iterator:
            yield chunk
