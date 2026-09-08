import asyncio

import pytest

from practice.exercise1_fetch_documents import Document, fetch_documents


@pytest.mark.asyncio
async def test_preserves_order_deduplicates_and_maps_failures_to_none():
    calls: list[str] = []

    async def fetcher(doc_id: str) -> Document:
        calls.append(doc_id)
        if doc_id == "bad":
            raise RuntimeError("downstream failure")
        await asyncio.sleep({"a": 0.03, "b": 0.01}.get(doc_id, 0))
        return Document(id=doc_id, title=doc_id.upper())

    result = await fetch_documents(
        ["a", "b", "a", "bad", "b"],
        fetcher,
        max_concurrency=2,
        timeout_s=0.5,
    )

    assert result == [
        Document("a", "A"),
        Document("b", "B"),
        Document("a", "A"),
        None,
        Document("b", "B"),
    ]
    assert sorted(calls) == ["a", "b", "bad"]


@pytest.mark.asyncio
async def test_never_exceeds_concurrency_limit():
    in_flight = 0
    max_seen = 0
    lock = asyncio.Lock()

    async def fetcher(doc_id: str) -> Document:
        nonlocal in_flight, max_seen
        async with lock:
            in_flight += 1
            max_seen = max(max_seen, in_flight)
        await asyncio.sleep(0.03)
        async with lock:
            in_flight -= 1
        return Document(doc_id, doc_id)

    result = await fetch_documents(
        [str(i) for i in range(12)],
        fetcher,
        max_concurrency=3,
        timeout_s=1.0,
    )

    assert len(result) == 12
    assert max_seen <= 3


@pytest.mark.asyncio
async def test_individual_timeout_does_not_fail_batch():
    async def fetcher(doc_id: str) -> Document:
        if doc_id == "slow":
            await asyncio.sleep(0.20)
        else:
            await asyncio.sleep(0.005)
        return Document(doc_id, doc_id)

    result = await fetch_documents(
        ["ok", "slow", "ok2"],
        fetcher,
        max_concurrency=2,
        timeout_s=0.05,
    )

    assert result == [
        Document("ok", "ok"),
        None,
        Document("ok2", "ok2"),
    ]


@pytest.mark.asyncio
async def test_empty_input():
    async def fetcher(doc_id: str) -> Document:
        raise AssertionError("fetcher should not be called")

    assert await fetch_documents([], fetcher) == []
