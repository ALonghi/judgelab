"""Interview exercise: use a full-text index supplied by SQLite.

Read README.md, then run: python -m pytest -q tests/test_search.py
"""
import sqlite3

from models import FtsHit
from storage import make_match_query


def search_articles(connection: sqlite3.Connection, query: str, *,
                    user_id: str, limit: int = 20) -> list[FtsHit]:
    """Return readable full-text matches from one customer's database.

    1. Validate 1 <= limit <= 100 first, including for an empty query.
       limit is an int; raise ValueError when outside that range.
    2. Use make_match_query(query). It returns a safe FTS expression requiring
       all distinct English letter/digit words, or None when there are none.
       Return [] for None. Do not implement a tokenizer or query language.
    3. Use articles MATCH ? to search the stored title/body index.
    4. Require public = 1 OR an existing grant for user_id and articles.rowid.
       Check access in SQL before LIMIT. Bind values; never format them into SQL.
    5. Order by rank ASC, then document_id ASC. FTS5's lower rank is better.
       Use the default rank. Do not recompute the earlier exercise's 3:1 score.
    6. Apply LIMIT in SQL. Fetch at most limit result rows into Python and map
       document_id/title to FtsHit. Return [] when nothing matches.
    Do not write, commit, rollback or close the connection. Document IDs are
    unique in this database. The caller already selected the correct customer's
    database and verified user_id. Setup and index updates are provided.
    """
    raise NotImplementedError('Use the supplied FTS5 index')
