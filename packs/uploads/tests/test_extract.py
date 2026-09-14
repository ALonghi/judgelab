import pytest
from extract import extract_lines
from indexing import open_index, index_revision


def test_split_utf8_and_lines():
    data = 'Café\n契約\nlast'.encode()
    assert list(extract_lines((data[i:i+1] for i in range(len(data))), max_line_chars=8)) == ['Café', '契約', 'last']


def test_empty_blocks_lines_and_preserved_whitespace():
    assert list(extract_lines(iter([b'', b'\n a \r\n\n', b'']), max_line_chars=4)) == [' a \r']
    assert list(extract_lines(iter(()), max_line_chars=1)) == []


def test_yields_before_consuming_next_block():
    advanced = False
    def blocks():
        nonlocal advanced
        yield b'one\ntwo\n'
        advanced = True
        yield b'three'
    lines = extract_lines(blocks(), max_line_chars=5)
    assert next(lines) == 'one' and not advanced
    assert next(lines) == 'two' and not advanced
    assert list(lines) == ['three'] and advanced


@pytest.mark.parametrize('data', [[b'\xff'], [b'\xe2', b'\x82']])
def test_invalid_or_truncated_utf8(data):
    with pytest.raises(UnicodeDecodeError):
        list(extract_lines(iter(data), max_line_chars=10))


@pytest.mark.parametrize('data', [[b'abcd\n'], [b'ab', b'cd'], [b'abcd']])
def test_rejects_oversized_complete_and_pending_lines(data):
    with pytest.raises(ValueError):
        list(extract_lines(iter(data), max_line_chars=3))


@pytest.mark.parametrize('limit', [0, -1])
def test_validate_before_consuming(limit):
    with pytest.raises(ValueError):
        next(extract_lines(None, max_line_chars=limit))


def test_prior_lines_remain_visible_before_later_failure():
    lines = extract_lines(iter([b'ok\n', b'toolong']), max_line_chars=2)
    assert next(lines) == 'ok'
    with pytest.raises(ValueError):
        next(lines)


def test_index_transaction_rollback_reopen_and_stale_revision(tmp_path):
    path = str(tmp_path / 'tenant.sqlite')
    db = open_index(path)
    assert index_revision(db, 'd', 1, extract_lines(iter([b'lease notice\n']), max_line_chars=20))
    with pytest.raises(UnicodeDecodeError):
        index_revision(db, 'd', 2, extract_lines(iter([b'replacement\n', b'\xff']), max_line_chars=20))
    assert db.execute('SELECT version FROM revisions').fetchone() == (1,)
    db.close()
    db = open_index(path)
    assert db.execute('SELECT document_id FROM sections WHERE sections MATCH ?', ('notice',)).fetchall() == [('d',)]
    assert index_revision(db, 'd', 3, iter(()))
    assert not index_revision(db, 'd', 2, iter(['stale notice']))
    assert db.execute('SELECT count(*) FROM sections').fetchone() == (0,)
    db.close()
