import asyncio

import pytest

from practice.exercise4_llm_stream import stream_with_fallback


async def collect(aiter):
    return [chunk async for chunk in aiter]


@pytest.mark.asyncio
async def test_primary_success_streams_without_using_fallback():
    fallback_called = False

    async def primary():
        yield "hello"
        await asyncio.sleep(0)
        yield " world"

    async def fallback():
        nonlocal fallback_called
        fallback_called = True
        yield "fallback"

    result = await collect(stream_with_fallback(primary, fallback))
    assert result == ["hello", " world"]
    assert fallback_called is False


@pytest.mark.asyncio
async def test_failure_before_first_chunk_uses_fallback():
    async def primary():
        if False:
            yield ""  # make this an async generator
        raise RuntimeError("provider unavailable")

    async def fallback():
        yield "backup"
        yield " answer"

    result = await collect(stream_with_fallback(primary, fallback))
    assert result == ["backup", " answer"]


@pytest.mark.asyncio
async def test_failure_after_partial_output_is_propagated():
    async def primary():
        yield "partial"
        raise RuntimeError("stream died")

    async def fallback():
        yield "should not happen"

    with pytest.raises(RuntimeError, match="stream died"):
        await collect(stream_with_fallback(primary, fallback))


@pytest.mark.asyncio
async def test_timeout_before_first_chunk_uses_fallback():
    async def primary():
        await asyncio.sleep(0.2)
        yield "late"

    async def fallback():
        yield "fast backup"

    result = await collect(
        stream_with_fallback(primary, fallback, chunk_timeout_s=0.03)
    )
    assert result == ["fast backup"]


@pytest.mark.asyncio
async def test_timeout_after_partial_output_is_propagated():
    async def primary():
        yield "first"
        await asyncio.sleep(0.2)
        yield "late"

    async def fallback():
        yield "nope"

    with pytest.raises(TimeoutError):
        await collect(
            stream_with_fallback(primary, fallback, chunk_timeout_s=0.03)
        )
