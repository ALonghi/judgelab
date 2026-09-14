"""Reference: transfer only the remaining acknowledged range."""
from hashlib import sha256
from typing import BinaryIO
from storage import UploadSession


def upload_file(source: BinaryIO, session: UploadSession, *, part_size: int) -> int:
    if part_size < 1:
        raise ValueError('part_size must be positive')
    offset = session.offset
    if offset < session.total_size:
        source.seek(offset)
    while offset < session.total_size:
        data = source.read(min(part_size, session.total_size - offset))
        if not data:
            raise EOFError('Source ended before declared size')
        session.put(offset, data, sha256(data).hexdigest())
        offset += len(data)
    session.complete()
    return offset
