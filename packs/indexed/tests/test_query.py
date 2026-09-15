import sqlite3
import pytest
from search_index import search_index
from conftest import seed


def search(db, query="notice", **kwargs):
    return search_index(db, query, tenant_id="a", user_id="alice", **kwargs)


def test_query_sums_distinct_query_terms_without_body_read(db):
    seed(db, "d", {"notice": 4, "lease": 3}, text="unrelated")
    db.set_authorizer(lambda action, table, *args:
                      sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ and table == "chunk_texts"
                      else sqlite3.SQLITE_OK)
    hits = search(db, "NOTICE notice lease!")
    assert [(h.tenant_id, h.document_id, h.chunk_id, h.title, h.score) for h in hits] == [("a", "d", "0", "d", 7)]


def test_query_or_matching_and_whole_tokens(db):
    seed(db, "a", {"notice": 1})
    seed(db, "b", {"lease": 3})
    seed(db, "c", {"notices": 4})
    assert [(h.document_id, h.score) for h in search(db, "notice lease")] == [("b", 3), ("a", 1)]


def test_query_permissions_before_limit_and_no_duplicate_grants(db):
    seed(db, "other", {"notice": 4}, tenant="b")
    seed(db, "secret", {"notice": 4}, public=False, allowed=("bob",))
    seed(db, "shared", {"notice": 3}, public=False, allowed=("alice", "bob"))
    seed(db, "public", {"notice": 1})
    assert [(h.document_id, h.score) for h in search(db, limit=2)] == [("shared", 3), ("public", 1)]


def test_query_ties_by_document_then_chunk(db):
    for doc, chunk in [("z", "0"), ("a", "2"), ("a", "1")]:
        seed(db, doc, {"notice": 1}, chunk=chunk)
    assert [(h.document_id, h.chunk_id) for h in search(db)] == [("a", "1"), ("a", "2"), ("z", "0")]


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_query_validates_limit_before_empty_query(db, limit):
    with pytest.raises(ValueError):
        search(db, "", limit=limit)


@pytest.mark.parametrize("query", ["", "!?", "unmatched"])
def test_query_empty_or_missing_terms(db, query):
    seed(db, "d", {"notice": 1})
    assert search(db, query) == []


def test_query_binds_identity_values_and_does_not_write(db):
    tenant = "a' OR 1=1 --"
    seed(db, "own", {"notice": 3}, tenant=tenant, public=False, allowed=("u'",))
    seed(db, "other", {"notice": 4})
    before = db.total_changes
    result = search_index(db, "notice", tenant_id=tenant, user_id="u'")
    assert [h.document_id for h in result] == ["own"]
    assert db.total_changes == before
    assert db.in_transaction


class RowBudget:
    """Observe rows crossing from SQLite to Python, not wall-clock timing."""
    def __init__(self, db, maximum):
        self.db, self.maximum, self.read = db, maximum, 0
    def execute(self, *args, **kwargs):
        return CountedCursor(self.db.execute(*args, **kwargs), self)


class CountedCursor:
    def __init__(self, cursor, budget):
        self.cursor, self.budget = cursor, budget
    def __iter__(self):
        return self
    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row
    def fetchone(self):
        row = self.cursor.fetchone()
        if row is not None:
            self.budget.read += 1
            assert self.budget.read <= self.budget.maximum, "Fetched candidates into Python before applying SQL LIMIT"
        return row
    def fetchall(self):
        return list(self)
    def fetchmany(self, size=1):
        result = []
        for _ in range(size):
            row = self.fetchone()
            if row is None:
                break
            result.append(row)
        return result


def test_query_only_top_rows_cross_into_python(db):
    for i in range(400):
        seed(db, f"{i:04}", {"notice": 1})
    guarded = RowBudget(db, 2)
    assert [h.document_id for h in search(guarded, limit=2)] == ["0000", "0001"]
    assert guarded.read == 2


def test_query_uses_term_lookup_plan(db):
    for i in range(300):
        seed(db, str(i), {"noise": 1})
    seed(db, "winner", {"rare": 3})
    queries = []
    db.set_trace_callback(queries.append)
    assert [h.document_id for h in search(db, "rare")] == ["winner"]
    db.set_trace_callback(None)
    plans = [row[3] for sql in queries if sql.lstrip().upper().startswith("SELECT")
             for row in db.execute("EXPLAIN QUERY PLAN " + sql)]
    assert any("SEARCH" in plan and "tenant_id=? AND term=?" in plan for plan in plans), plans
