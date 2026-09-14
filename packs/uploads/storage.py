"""Supplied local storage adapter. No credentials, network or object-store SDK."""
from hashlib import sha256
from pathlib import Path


class UploadSession:
    """One immutable source, one writer. The path contains acknowledged bytes.

    This local stand-in validates each part before appending it. It is not a
    durable cloud session protocol: process crashes and concurrent writers are
    outside its contract. Reuse the session after an ordinary transfer failure.
    """
    def __init__(self, path: Path, total_size: int):
        self.path = path
        self.total_size = total_size
        self.completed = False
        self.aborted = False
        self.path.touch(exist_ok=False)

    @property
    def offset(self) -> int:
        return self.path.stat().st_size

    def put(self, offset: int, data: bytes, checksum: str) -> None:
        if self.aborted or self.completed:
            raise ValueError('Session is closed')
        if offset != self.offset or not data:
            raise ValueError('Wrong offset or empty part')
        if sha256(data).hexdigest() != checksum:
            raise ValueError('Part checksum mismatch')
        if offset + len(data) > self.total_size:
            raise ValueError('Part exceeds declared size')
        with self.path.open('ab') as target:
            target.write(data)

    def complete(self) -> None:
        if self.aborted or self.offset != self.total_size:
            raise ValueError('Cannot complete an incomplete or aborted upload')
        self.completed = True

    def abort(self) -> None:
        self.path.unlink(missing_ok=True)
        self.aborted = True
