"""Reference checkpoint 2: aggregate in SQLite and return only the top rows."""
import sqlite3
from models import IndexedHit
from text_tools import terms


def search_index(connection: sqlite3.Connection, query: str, *,
                 tenant_id: str, user_id: str, limit: int = 20) -> list[IndexedHit]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    query_terms = sorted(terms(query))
    if not query_terms:
        return []
    placeholders = ",".join("?" for _ in query_terms)
    # Only placeholder syntax is generated; every user value is bound.
    rows = connection.execute(f"""
        SELECT u.tenant_id, u.document_id, u.chunk_id, u.title, SUM(p.weight) AS score
        FROM postings p JOIN units u ON u.id = p.unit_id
        WHERE p.tenant_id = ? AND u.tenant_id = ?
          AND p.term IN ({placeholders})
          AND (u.public = 1 OR EXISTS (
              SELECT 1 FROM grants g WHERE g.unit_id = u.id AND g.user_id = ?
          ))
        GROUP BY u.id
        ORDER BY score DESC, u.document_id ASC, u.chunk_id ASC
        LIMIT ?
    """, (tenant_id, tenant_id, *query_terms, user_id, limit))
    return [IndexedHit(*row) for row in rows]
