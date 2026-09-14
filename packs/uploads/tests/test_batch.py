import asyncio
import pytest
from batch import upload_batch
from models import UploadResult


@pytest.mark.asyncio
async def test_concurrent_order_and_partial_failure():
    both = asyncio.Event()
    active = 0
    peak = 0
    async def upload(file_id):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        if active == 2:
            both.set()
        try:
            await asyncio.wait_for(both.wait(), 1)
            if file_id == 'bad':
                raise OSError('offline')
            await asyncio.sleep(0)
        finally:
            active -= 1
    result = await upload_batch(iter(['a', 'bad', 'c']), upload, workers=2)
    assert result == [UploadResult('a'), UploadResult('bad', 'offline'), UploadResult('c')]
    assert peak == 2 and active == 0


@pytest.mark.asyncio
async def test_bounds_consumption_and_tasks():
    baseline = set(asyncio.all_tasks())
    consumed = finished = 0
    def inputs():
        nonlocal consumed
        for number in range(1000):
            consumed += 1
            assert consumed - finished <= 3, 'Do not eagerly consume the input'
            yield str(number)
    async def upload(file_id):
        nonlocal finished
        assert len(set(asyncio.all_tasks()) - baseline) <= 3, 'Too many child tasks'
        await asyncio.sleep(0)
        finished += 1
    result = await upload_batch(inputs(), upload, workers=3)
    assert len(result) == 1000 and finished == 1000


@pytest.mark.asyncio
async def test_empty_input():
    async def upload(file_id):
        pytest.fail('No upload expected')
    assert await upload_batch(iter(()), upload, workers=2) == []


@pytest.mark.asyncio
@pytest.mark.parametrize('workers', [0, -1])
async def test_validate_before_consuming(workers):
    with pytest.raises(ValueError):
        await upload_batch(None, None, workers=workers)


@pytest.mark.asyncio
async def test_parent_cancellation_awaits_children():
    ready = asyncio.Event()
    live = set()
    cleaned = set()
    async def upload(file_id):
        live.add(file_id)
        if len(live) == 2:
            ready.set()
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0)
            live.remove(file_id)
            cleaned.add(file_id)
    task = asyncio.create_task(upload_batch(iter(['a', 'b', 'c']), upload, workers=2))
    await asyncio.wait_for(ready.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not live and cleaned == {'a', 'b'}


@pytest.mark.asyncio
async def test_iterator_failure_cleans_up_uploads():
    live = set()
    def broken():
        yield 'a'
        raise RuntimeError('manifest unavailable')
    async def upload(file_id):
        live.add(file_id)
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0)
            live.remove(file_id)
    with pytest.raises(RuntimeError, match='manifest unavailable'):
        await upload_batch(broken(), upload, workers=2)
    assert not live


@pytest.mark.asyncio
async def test_child_cancellation_propagates():
    async def upload(file_id):
        raise asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        await upload_batch(['a'], upload, workers=1)
