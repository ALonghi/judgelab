"""Provided SQLite schema and adapters. No external database service needed."""
import sqlite3
from collections.abc import Iterable, Iterator
from pathlib import Path

from models import Chunk, Document, IndexedHit, SearchUnit


SCHEMA = """
CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    title TEXT NOT NULL,
    public INTEGER NOT NULL CHECK (public IN (0, 1)),
    UNIQUE (tenant_id, document_id, chunk_id)
);
CREATE TABLE IF NOT EXISTS contents (
    unit_id INTEGER PRIMARY KEY REFERENCES units(id),
    text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS grants (
    unit_id INTEGER NOT NULL REFERENCES units(id),
    user_id TEXT NOT NULL,
    PRIMARY KEY (unit_id, user_id)
);
CREATE TABLE IF NOT EXISTS postings (
    tenant_id TEXT NOT NULL,
    term TEXT NOT NULL,
    unit_id INTEGER NOT NULL REFERENCES units(id),
    weight INTEGER NOT NULL CHECK (weight IN (1, 3, 4)),
    PRIMARY KEY (tenant_id, term, unit_id)
);
"""


def open_index(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA cache_size = -2048")
    connection.execute("PRAGMA temp_store = FILE")
    connection.executescript(SCHEMA)
    return connection


def document_units(documents: Iterable[Document]) -> Iterator[SearchUnit]:
    """Use whole documents for the first two checkpoints, one at a time."""
    for doc in documents:
        yield SearchUnit(doc.tenant_id, doc.document_id, "", doc.title,
                         doc.text, doc.public, doc.allowed_users)


def load_chunks(connection: sqlite3.Connection, hits: Iterable[IndexedHit], *,
                tenant_id: str, user_id: str) -> Iterator[Chunk]:
    """Load text only for returned hits, in rank order, rechecking access.

    This is the adapter to the existing build_context contract. Its input can
    also contain whole-document hits, but context practice should use chunks.
    It preserves order; it does not re-rank or truncate text.
    """
    for hit in hits:
        if hit.tenant_id != tenant_id:
            continue
        row = connection.execute("""
            SELECT c.text FROM units u JOIN contents c ON c.unit_id = u.id
            WHERE u.tenant_id = ? AND u.document_id = ? AND u.chunk_id = ?
              AND (u.public = 1 OR EXISTS (
                SELECT 1 FROM grants g WHERE g.unit_id = u.id AND g.user_id = ?
              ))
        """, (tenant_id, hit.document_id, hit.chunk_id, user_id)).fetchone()
        if row is not None:
            # Access was checked for this user; retain that scope in the chunk.
            yield Chunk(tenant_id, hit.document_id, hit.chunk_id, row[0],
                        frozenset({user_id}), False)
