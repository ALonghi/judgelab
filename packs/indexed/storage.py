"""Provided normalized SQLite schema and adapter to context selection."""
import sqlite3
from collections.abc import Iterable, Iterator
from pathlib import Path
from models import Chunk, IndexedHit


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    tenant_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    title TEXT NOT NULL,
    public INTEGER NOT NULL CHECK (public IN (0, 1)),
    PRIMARY KEY (tenant_id, document_id)
);
CREATE TABLE IF NOT EXISTS document_access (
    tenant_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    PRIMARY KEY (tenant_id, document_id, user_id),
    FOREIGN KEY (tenant_id, document_id) REFERENCES documents(tenant_id, document_id)
);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL CHECK (chunk_id <> ''),
    UNIQUE (tenant_id, document_id, chunk_id),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, document_id) REFERENCES documents(tenant_id, document_id)
);
CREATE TABLE IF NOT EXISTS chunk_texts (
    chunk_pk INTEGER PRIMARY KEY REFERENCES chunks(id),
    text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS term_chunks (
    tenant_id TEXT NOT NULL,
    term TEXT NOT NULL,
    chunk_pk INTEGER NOT NULL,
    weight INTEGER NOT NULL CHECK (weight IN (1, 3, 4)),
    PRIMARY KEY (tenant_id, term, chunk_pk),
    FOREIGN KEY (tenant_id, chunk_pk) REFERENCES chunks(tenant_id, id)
);
"""


def open_index(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA cache_size = -2048")
    connection.execute("PRAGMA temp_store = FILE")
    connection.executescript(SCHEMA)
    return connection


def load_chunks(connection: sqlite3.Connection, hits: Iterable[IndexedHit], *,
                tenant_id: str, user_id: str) -> Iterator[Chunk]:
    """Fetch only returned text, in rank order, rechecking document access.

    Chunk is the existing context exercise's boundary record. Its access fields
    carry the checked caller scope; they are not duplicate stored permissions.
    """
    for hit in hits:
        if hit.tenant_id != tenant_id:
            continue
        row = connection.execute("""
            SELECT t.text FROM chunks c
            JOIN documents d USING (tenant_id, document_id)
            JOIN chunk_texts t ON t.chunk_pk = c.id
            WHERE c.tenant_id = ? AND c.document_id = ? AND c.chunk_id = ?
              AND (d.public = 1 OR EXISTS (
                SELECT 1 FROM document_access a
                WHERE a.tenant_id = d.tenant_id AND a.document_id = d.document_id
                  AND a.user_id = ?
              ))
        """, (tenant_id, hit.document_id, hit.chunk_id, user_id)).fetchone()
        if row is not None:
            yield Chunk(tenant_id, hit.document_id, hit.chunk_id, row[0],
                        frozenset({user_id}), False)
