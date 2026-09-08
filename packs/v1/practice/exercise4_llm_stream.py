from __future__ import annotations

from collections.abc import AsyncIterator, Callable


StreamFactory = Callable[[], AsyncIterator[str]]


async def stream_with_fallback(
    primary: StreamFactory,
    fallback: StreamFactory,
    *,
    chunk_timeout_s: float = 1.0,
) -> AsyncIterator[str]:
    """
    Exercise 4: LLM-style streaming with fallback.

    The function returns an async iterator of text chunks.

    Requirements
    ------------
    1. Start consuming the primary stream.
    2. Each individual wait for the next chunk must time out after
       `chunk_timeout_s`.
    3. If primary fails/times out BEFORE yielding any chunk:
         -> switch to fallback and yield fallback chunks.
    4. If primary has already yielded at least one chunk and then fails/times out:
         -> propagate the error; DO NOT silently switch providers.
       Reason: mixing partial output from two models can create nonsense.
    5. Errors from fallback propagate normally.
    6. Do not swallow asyncio.CancelledError.
    7. Do not buffer the entire response before yielding it.

    You may create private helper functions.

    Interview follow-ups
    --------------------
    - Would you retry the same provider before falling back?
    - What would you log/measure for each generation?
    - How would SSE/WebSocket client disconnect propagate cancellation?
    - How would you handle a provider that returns HTTP 429?
    - When would transparent fallback be unsafe even before the first token?
    - How could you version prompts/model parameters for reproducibility?
    """
    raise NotImplementedError("Implement exercise 4")
