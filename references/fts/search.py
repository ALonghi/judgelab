"""One FTS5 query with access control and ranking inside SQLite."""
import sqlite3

from models import FtsHit
from storage import make_match_query


def search_articles(connection: sqlite3.Connection, query: str, *,
                    user_id: str, limit: int = 20) -> list[FtsHit]:
    if not 1 <= limit <= 100:
        raise ValueError('limit must be in 1..100')
    expression = make_match_query(query)
    if expression is None:
        return []
    rows = connection.execute('''
        SELECT document_id, title
        FROM articles
        WHERE articles MATCH ?
          AND (public = 1 OR EXISTS (
              SELECT 1 FROM grants
              WHERE grants.article_rowid = articles.rowid AND grants.user_id = ?
          ))
        ORDER BY rank ASC, document_id ASC
        LIMIT ?
    ''', (expression, user_id, limit))
    return [FtsHit(*row) for row in rows]
