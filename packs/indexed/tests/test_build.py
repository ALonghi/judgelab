import sqlite3
import pytest
from build_index import build_index
from models import Document, DocumentChunk
from storage import open_index


def chunk(key, title="", text="", **kwargs):
    return DocumentChunk(Document("a", key, title, **kwargs), "0", text)


def test_build_weights_whole_terms_and_repetition(db):
    assert build_index(db, [chunk("d", "NOTICE notice", "Notice of notices!")]) == 1
    assert db.execute("SELECT term, weight FROM term_chunks ORDER BY term").fetchall() == [
        ("notice", 4), ("notices", 1), ("of", 1)]


def test_build_title_only_body_only_and_overlap(db):
    build_index(db, [chunk("d", "lease notice", "notice period")])
    assert dict(db.execute("SELECT term, weight FROM term_chunks")) == {
        "lease": 3, "notice": 4, "period": 1}


def test_build_metadata_body_and_grants(db):
    original = DocumentChunk(Document("firm", "d", "Title", False,
                          frozenset({"alice", "bob"})), "c2", "Exact  text!")
    build_index(db, [original])
    assert db.execute("SELECT c.tenant_id, c.document_id, c.chunk_id, d.title, d.public FROM chunks c JOIN documents d USING (tenant_id, document_id)").fetchone() == (
        "firm", "d", "c2", "Title", 0)
    assert db.execute("SELECT text FROM chunk_texts").fetchone() == ("Exact  text!",)
    assert list(db.execute("SELECT user_id FROM document_access ORDER BY user_id")) == [("alice",), ("bob",)]
    assert original.text == "Exact  text!"


def test_build_composite_identity_and_blank_chunks(db):
    chunks = [DocumentChunk(Document("a", "d", "X"), "0", "!?"),
             DocumentChunk(Document("a", "d", "X"), "1", ""),
             DocumentChunk(Document("b", "d", ""), "0", "")]
    assert build_index(db, iter(chunks)) == 3
    assert db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 3
    assert db.execute("SELECT COUNT(*) FROM term_chunks").fetchone()[0] == 2


def test_build_writes_before_requesting_next_chunk(db):
    def one_pass():
        yield chunk("1", "first", "body")
        assert db.execute("SELECT COUNT(*) FROM term_chunks").fetchone()[0] == 2, "Input was buffered before indexing"
        yield chunk("2", "second", "body")
    assert build_index(db, one_pass()) == 2


def test_build_leaves_transaction_control_to_caller(db):
    db.execute("BEGIN")
    build_index(db, [chunk("1", "lease")])
    assert db.in_transaction
    db.rollback()
    assert db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0


def test_build_persists_after_reopen(tmp_path):
    path = tmp_path / "persist.sqlite"
    db = open_index(path)
    with db:
        build_index(db, [chunk("d", "lease")])
    db.close()
    reopened = open_index(path)
    try:
        assert reopened.execute("SELECT term, weight FROM term_chunks").fetchone() == ("lease", 3)
    finally:
        reopened.close()


def test_build_empty_input(db):
    assert build_index(db, iter(())) == 0


def test_build_duplicate_identity_rolls_back_in_caller_transaction(db):
    with pytest.raises(sqlite3.IntegrityError):
        with db:
            build_index(db, [chunk("d", "first"), chunk("d", "first")])
    assert db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 0


def test_build_stores_document_and_access_once_across_chunks_and_calls(db):
    doc = Document("a", "d", "Shared title", False, frozenset({"alice", "bob"}))
    assert build_index(db, [DocumentChunk(doc, "0", "first")]) == 1
    assert build_index(db, [DocumentChunk(doc, "1", "second")]) == 1
    assert db.execute("SELECT * FROM documents").fetchall() == [("a", "d", "Shared title", 0)]
    assert db.execute("SELECT COUNT(*) FROM document_access").fetchone()[0] == 2
    assert db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 2
    assert db.execute("SELECT text FROM chunk_texts ORDER BY chunk_pk").fetchall() == [("first",), ("second",)]


def test_build_many_chunks_from_interleaved_documents(db):
    a, b = Document("a", "same", "A"), Document("b", "same", "B")
    def chunks():
        for i in range(200):
            assert db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] == 2 * i
            yield DocumentChunk(a, str(i), "text")
            yield DocumentChunk(b, str(i), "text")
    assert build_index(db, chunks()) == 400
    assert db.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 2
