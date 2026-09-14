"""Reference: fixed workers claim one input item before each awaited upload."""
import asyncio
from collections.abc import Awaitable, Callable, Iterable
from models import UploadResult


async def upload_batch(file_ids: Iterable[str], upload: Callable[[str], Awaitable[None]],
                       *, workers: int) -> list[UploadResult]:
    if workers < 1:
        raise ValueError('workers must be positive')
    source = iter(file_ids)
    results = []

    async def worker():
        while True:
            try:
                file_id = next(source)
            except StopIteration:
                return
            position = len(results)
            results.append(None)
            try:
                await upload(file_id)
            except Exception as error:
                results[position] = UploadResult(file_id, str(error))
            else:
                results[position] = UploadResult(file_id)

    tasks = [asyncio.create_task(worker()) for _ in range(workers)]
    try:
        await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    return results
