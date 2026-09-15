"""Lifecycle checks beyond the original streaming exercise's five cases."""
import asyncio
import runpy
from pathlib import Path

import pytest

stream_with_fallback = runpy.run_path(str(
    Path(__file__).resolve().parents[1]
    / 'references/v1/practice/exercise4_llm_stream.py'
))['stream_with_fallback']


@pytest.mark.asyncio
@pytest.mark.parametrize('empty_chunk', [False, True])
async def test_empty_completion_or_chunk_does_not_enable_backup(empty_chunk):
    async def primary():
        if empty_chunk:
            yield ''
            raise RuntimeError('after empty chunk')

    def backup():
        pytest.fail('Backup must not start')

    stream = stream_with_fallback(primary, backup)
    if empty_chunk:
        assert await anext(stream) == ''
        with pytest.raises(RuntimeError, match='after empty chunk'):
            await anext(stream)
    else:
        assert [chunk async for chunk in stream] == []


@pytest.mark.asyncio
async def test_backup_timeout_closes_both_providers():
    closed = []

    async def primary():
        try:
            raise RuntimeError('unavailable')
            yield
        finally:
            closed.append('primary')

    async def backup():
        try:
            await asyncio.Event().wait()
            yield
        finally:
            closed.append('backup')

    with pytest.raises(TimeoutError):
        await anext(stream_with_fallback(primary, backup, chunk_timeout_s=0.01))
    assert closed == ['primary', 'backup']


@pytest.mark.asyncio
async def test_cancellation_closes_primary_without_starting_backup():
    started = asyncio.Event()
    closed = asyncio.Event()

    async def primary():
        try:
            started.set()
            await asyncio.Event().wait()
            yield
        finally:
            closed.set()

    def backup():
        pytest.fail('Cancellation must not start backup')

    task = asyncio.create_task(anext(stream_with_fallback(primary, backup)))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert closed.is_set()


@pytest.mark.asyncio
async def test_explicit_close_releases_paused_provider():
    closed = []

    async def primary():
        try:
            yield 'first'
            pytest.fail('Must not read ahead')
        finally:
            closed.append(True)

    stream = stream_with_fallback(primary, primary)
    assert await anext(stream) == 'first'
    await stream.aclose()
    assert closed == [True]
