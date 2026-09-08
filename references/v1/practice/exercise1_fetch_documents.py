from __future__ import annotations
import asyncio
import math

from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable


@dataclass(frozen=True)
class Document:
    id: str
    title: str


FetchDocument = Callable[[str], Awaitable[Document]]


async def fetch_documents(ids: Iterable[str], fetcher: FetchDocument, *,
                          max_concurrency: int = 5,
                          timeout_s: float = 2.0) -> list[Document | None]:
    if max_concurrency < 1 or not math.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError("Invalid concurrency or timeout")
    ordered_ids = list(ids)
    unique_ids = list(dict.fromkeys(ordered_ids))
    semaphore = asyncio.Semaphore(max_concurrency)

    async def fetch_one(document_id):
        try:
            async with semaphore:
                async with asyncio.timeout(timeout_s):
                    return await fetcher(document_id)
        except Exception:
            return None

    async with asyncio.TaskGroup() as group:
        tasks = {key: group.create_task(fetch_one(key)) for key in unique_ids}
    return [tasks[key].result() for key in ordered_ids]
