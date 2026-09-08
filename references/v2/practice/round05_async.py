import asyncio
import math
"""Optional deeper extension. Read prompts/05_async.md, then run:
    python -m pytest -q tests/test_05_async.py -x
Suggested time: 30-40 minutes. Explore concurrency and failure handling.
"""
from collections.abc import Awaitable, Callable, Mapping
from practice.models import Candidate, FederatedResult


type SearchSource = Callable[[str], Awaitable[list[Candidate]]]


async def federated_search(query: str, sources: Mapping[str, SearchSource], *,
                           max_concurrency: int = 3,
                           timeout_s: float = 1.0) -> FederatedResult:
    if max_concurrency < 1 or not math.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError("Invalid concurrency or timeout")
    semaphore = asyncio.Semaphore(max_concurrency)

    async def call(name, source):
        try:
            async with semaphore:
                async with asyncio.timeout(timeout_s):
                    return name, await source(query), False
        except Exception:
            # CancelledError is not converted to an ordinary source failure.
            return name, [], True

    # A task group owns and awaits children, including during cancellation.
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(call(name, source)) for name, source in sources.items()]
    best = {}
    failed = []
    for task in tasks:
        name, hits, has_failed = task.result()
        if has_failed:
            failed.append(name)
        for hit in hits:
            key = (hit.tenant_id, hit.document_id)
            if key not in best or hit.score > best[key].score:
                best[key] = hit
    ordered = sorted(best.values(), key=lambda hit: (-hit.score, hit.tenant_id, hit.document_id))
    return FederatedResult(tuple(ordered), tuple(sorted(failed)))
