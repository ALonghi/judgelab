"""Checkpoint 1: resume an immutable file using bounded reads."""
from hashlib import sha256
from typing import BinaryIO
from storage import UploadSession


def upload_file(source: BinaryIO, session: UploadSession, *, part_size: int) -> int:
    """Return total acknowledged bytes after completion.

    part_size is an int: reject < 1 before touching source or session.
    The caller supplies a seekable binary source that does not change between
    attempts, and a session belonging to that source and trusted tenant.
    Seek to session.offset, then read at most part_size bytes per call, stopping
    at total_size. Short nonempty reads are valid. An empty read before total_size
    raises EOFError. Do not read past the declared size or read a completed file.
    For each part, call put(offset, data, sha256(data).hexdigest()). Advance only
    after acknowledgment. Complete only after all declared bytes are stored.
    A zero-byte file still needs complete(). Return total_size.
    Propagate storage/source errors; retain acknowledged parts for a later call.
    Do not retry internally, abort, close the source, or buffer the whole file.
    The session may have accepted a part before its reply failed. A later call
    must obtain its current offset again. Completion is safe to repeat.
    """
    raise NotImplementedError('Resume a bounded upload')
