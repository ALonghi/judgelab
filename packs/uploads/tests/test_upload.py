import io
from hashlib import sha256
import pytest
from storage import UploadSession
from upload import upload_file


class BoundedSource(io.BytesIO):
    def read(self, size=-1):
        assert 0 < size <= 4, 'Use bounded reads'
        return super().read(min(size, 2))  # Real streams may return short reads.


def test_upload_short_reads_checksum_and_completion(tmp_path):
    session = UploadSession(tmp_path / 'blob', 9)
    source = BoundedSource(b'abcdefghiEXTRA')
    assert upload_file(source, session, part_size=4) == 9
    assert session.path.read_bytes() == b'abcdefghi'
    assert session.completed and not source.closed
    assert source.tell() == 9


def test_upload_empty_and_repeated_completion(tmp_path):
    session = UploadSession(tmp_path / 'blob', 0)
    class NoRead:
        def read(self, *args):
            pytest.fail('Completed input must not be read')
    assert upload_file(NoRead(), session, part_size=4) == 0
    assert upload_file(NoRead(), session, part_size=4) == 0
    assert session.completed


def test_resume_after_accepted_part_lost_reply(tmp_path):
    class LostReply(UploadSession):
        fail = True
        def put(self, offset, data, checksum):
            super().put(offset, data, checksum)
            if self.fail:
                self.fail = False
                raise OSError('reply lost')
    session = LostReply(tmp_path / 'blob', 8)
    source = BoundedSource(b'abcdefgh')
    with pytest.raises(OSError, match='reply lost'):
        upload_file(source, session, part_size=4)
    acknowledged = session.offset
    assert 0 < acknowledged <= 4
    assert session.path.read_bytes() == b'abcdefgh'[:acknowledged]
    assert not session.completed and not session.aborted
    assert upload_file(BoundedSource(b'abcdefgh'), session, part_size=4) == 8
    assert session.path.read_bytes() == b'abcdefgh'


def test_truncated_source_keeps_acknowledged_parts(tmp_path):
    session = UploadSession(tmp_path / 'blob', 8)
    session.put(0, b'a', sha256(b'a').hexdigest())
    with pytest.raises(EOFError):
        upload_file(BoundedSource(b'abc'), session, part_size=4)
    assert 1 <= session.offset <= 3
    assert session.path.read_bytes() == b'abc'[:session.offset]
    assert not session.completed and not session.aborted


@pytest.mark.parametrize('size', [0, -1])
def test_validate_before_touching_inputs(size):
    with pytest.raises(ValueError):
        upload_file(None, None, part_size=size)


def test_existing_offset_does_not_resend_prefix(tmp_path):
    session = UploadSession(tmp_path / 'blob', 6)
    session.put(0, b'ab', sha256(b'ab').hexdigest())
    assert upload_file(BoundedSource(b'abcdef'), session, part_size=4) == 6
    assert session.path.read_bytes() == b'abcdef'


def test_logically_large_source_is_never_materialized():
    # Four GiB logical transfer, one reusable 1 MiB byte object; sink stores counts.
    block = b'x' * (1024 * 1024)
    class Source:
        position = 0
        def seek(self, offset):
            assert offset == 0
        def read(self, size):
            assert 0 < size <= len(block)
            assert self.position + size <= sink.total_size
            assert 0 <= self.position - sink.offset + size <= len(block), 'Buffer at most one unacknowledged part'
            self.position += size
            return block[:size]
    class Sink:
        offset = 0
        total_size = 4 * 1024**3
        completed = False
        def put(self, offset, data, checksum):
            assert offset == self.offset
            assert offset + len(data) <= source.position
            assert 0 < len(data) <= len(block)
            assert data == block[:len(data)]
            assert checksum == sha256(data).hexdigest()
            self.offset += len(data)
        def complete(self):
            assert self.offset == self.total_size == source.position
            self.completed = True
    sink = Sink()
    source = Source()
    assert upload_file(source, sink, part_size=len(block)) == sink.total_size
    assert sink.completed
