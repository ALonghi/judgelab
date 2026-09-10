import sqlite3
import pytest
from build_index import build_index
from models import SearchUnit
from storage import open_index


def unit(key, title="", text="", **kwargs):
    return SearchUnit("a", key, "", title, text, **kwargs)


def test_build_weights_whole_terms_and_repetition(db):
    assert build_index(db, [unit("d", "NOTICE notice", "Notice of notices!")]) == 1
    assert db.execute("SELECT term, weight FROM postings ORDER BY term").fetchall() == [
        ("notice", 4), ("notices", 1), ("of", 1)]


def test_build_title_only_body_only_and_overlap(db):
    build_index(db, [unit("d", "lease notice", "notice period")])
    assert dict(db.execute("SELECT term, weight FROM postings")) == {
        "lease": 3, "notice": 4, "period": 1}


def test_build_metadata_body_and_grants(db):
    original = SearchUnit("firm", "d", "c2", "Title", "Exact  text!", False,
                          frozenset({"alice", "bob"}))
    build_index(db, [original])
    assert db.execute("SELECT tenant_id, document_id, chunk_id, title, public FROM units").fetchone() == (
        "firm", "d", "c2", "Title", 0)
    assert db.execute("SELECT text FROM contents").fetchone() == ("Exact  text!",)
    assert list(db.execute("SELECT user_id FROM grants ORDER BY user_id")) == [("alice",), ("bob",)]
    assert original.text == "Exact  text!"


def test_build_composite_identity_and_blank_units(db):
    units = [SearchUnit("a", "d", "0", "", "!?"),
             SearchUnit("a", "d", "1", "X", ""),
             SearchUnit("b", "d", "0", "X", "")]
    assert build_index(db, iter(units)) == 3
    assert db.execute("SELECT COUNT(*) FROM units").fetchone()[0] == 3
    assert db.execute("SELECT COUNT(*) FROM postings").fetchone()[0] == 2


def test_build_writes_before_requesting_next_unit(db):
    def one_pass():
        yield unit("1", "first", "body")
        assert db.execute("SELECT COUNT(*) FROM postings").fetchone()[0] == 2, "Input was buffered before indexing"
        yield unit("2", "second", "body")
    assert build_index(db, one_pass()) == 2


def test_build_leaves_transaction_control_to_caller(db):
    db.execute("BEGIN")
    build_index(db, [unit("1", "lease")])
    assert db.in_transaction
    db.rollback()
    assert db.execute("SELECT COUNT(*) FROM units").fetchone()[0] == 0


def test_build_persists_after_reopen(tmp_path):
    path = tmp_path / "persist.sqlite"
    db = open_index(path)
    with db:
        build_index(db, [unit("d", "lease")])
    db.close()
    reopened = open_index(path)
    try:
        assert reopened.execute("SELECT term, weight FROM postings").fetchone() == ("lease", 3)
    finally:
        reopened.close()


def test_build_empty_input(db):
    assert build_index(db, iter(())) == 0


def test_build_duplicate_identity_rolls_back_in_caller_transaction(db):
    with pytest.raises(sqlite3.IntegrityError):
        with db:
            build_index(db, [unit("d", "first"), unit("d", "second")])
    assert db.execute("SELECT COUNT(*) FROM units").fetchone()[0] == 0
