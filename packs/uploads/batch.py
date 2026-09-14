"""Checkpoint 2: bound allocated tasks as well as active uploads."""
import asyncio
from collections.abc import Awaitable, Callable, Iterable
from models import UploadResult


async def upload_batch(file_ids: Iterable[str], upload: Callable[[str], Awaitable[None]],
                       *, workers: int) -> list[UploadResult]:
    """Upload unique IDs from a finite, one-pass iterable; preserve input order.

    workers is an int; reject <1 before consuming input. At most workers upload
    calls AND at most workers child tasks may exist at once. Do not materialize
    input before starting work or create a task for each file. IDs are unique;
    deduplication is outside this contract. Return UploadResult(id) on success,
    UploadResult(id, str(error)) on an ordinary Exception and continue other files.
    No automatic retries. Input-iterator failures propagate.
    On cancellation or iterator failure, cancel AND await all owned tasks before
    returning control. Never convert CancelledError into an ordinary file failure.
    The uploader owns each file's resume state. This function owns scheduling.
    Returning a list costs O(number of files) metadata; file bytes stay in the
    supplied uploader. Production status storage/pagination is a follow-up.
    """
    raise NotImplementedError('Schedule a fixed worker pool')
