from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable


@dataclass(frozen=True)
class Document:
    id: str
    title: str


FetchDocument = Callable[[str], Awaitable[Document]]


async def fetch_documents(
    ids: Iterable[str],
    fetcher: FetchDocument,
    *,
    max_concurrency: int = 5,
    timeout_s: float = 2.0,
) -> list[Document | None]:
    """
    Exercise 1: bounded concurrent document fetching.

    Requirements
    ------------
    1. Fetch documents concurrently.
    2. Never have more than `max_concurrency` fetcher calls in flight.
    3. Apply `timeout_s` independently to each fetch.
    4. A timeout/error for one ID must produce None for that position,
       not fail the whole batch.
    5. Preserve the exact input order.
    6. Duplicate IDs must only trigger ONE downstream fetch, while still
       appearing multiple times in the returned list.
    7. Empty input should return [].

    Constraints
    -----------
    - Use asyncio; do not use threads.
    - Keep the public function signature unchanged.

    Interview follow-ups to answer after you pass the tests
    --------------------------------------------------------
    - What happens if `ids` contains 500,000 IDs?
    - Does a semaphore alone prevent creating 500,000 tasks?
    - How would you implement global concurrency limits across 20 processes?
    - Would you retry all failures? Which ones? With what backoff?
    - If the caller is cancelled, what should happen to child work?
    """
    raise NotImplementedError("Implement exercise 1")
