"""Checkpoint 2. Query the provided schema; tests seed it independently."""
import sqlite3
from models import IndexedHit
from text_tools import terms


def search_index(connection: sqlite3.Connection, query: str, *,
                 tenant_id: str, user_id: str, limit: int = 20) -> list[IndexedHit]:
    """Rank from postings, without loading document bodies into Python.

    Validate integer limit in 1..100 first, even for an empty query.
    Normalize query once with terms(). Empty terms -> []. Inputs have at most
    32 distinct terms. Query terms are OR matches, each contributes once.
    Filter tenant and (public OR user grant) before the result limit.
    Sum posting weights per unit. Return positive-scoring hits ordered by
    score DESC, document_id ASC, chunk_id ASC, taking limit LAST in SQL.
    Use parameter binding, never interpolate user strings into SQL.
    Execute ranking/aggregation/limiting in SQLite. Read at most limit result
    rows into Python; do not fetch all candidates and sort them in Python.
    Do not read contents or tokenize stored text; postings hold the scores.
    Do not modify, commit, rollback, or close the connection.
    Categories are deliberately out of scope in this pack.
    """
    raise NotImplementedError("Retrieve and score indexed matches")
