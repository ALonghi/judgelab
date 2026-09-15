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
    rows = connection.execute(f"""
        SELECT c.tenant_id, c.document_id, c.chunk_id, d.title, SUM(t.weight) AS score
        FROM term_chunks t JOIN chunks c ON c.id = t.chunk_pk AND c.tenant_id = t.tenant_id
        JOIN documents d ON d.tenant_id = c.tenant_id AND d.document_id = c.document_id
        WHERE t.tenant_id = ? AND t.term IN ({placeholders})
          AND (d.public = 1 OR EXISTS (
              SELECT 1 FROM document_access a
              WHERE a.tenant_id = d.tenant_id AND a.document_id = d.document_id
                AND a.user_id = ?
          ))
        GROUP BY c.id
        ORDER BY score DESC, c.document_id ASC, c.chunk_id ASC
        LIMIT ?
    """, (tenant_id, *query_terms, user_id, limit))
    return [IndexedHit(*row) for row in rows]
