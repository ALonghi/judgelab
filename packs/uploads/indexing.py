"""Supplied SQLite bridge: one tenant database, one writer, bounded text units.

For learning only: one transaction per document can hold a write lock for a long
extraction. Production alternatives stage a new revision in bounded transactions
and atomically switch the active revision after validation.
"""
import sqlite3
from collections.abc import Iterable


def open_index(path: str) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.executescript('''
        CREATE TABLE IF NOT EXISTS revisions(document_id TEXT PRIMARY KEY, version INTEGER);
        CREATE VIRTUAL TABLE IF NOT EXISTS sections USING fts5(
            document_id UNINDEXED, version UNINDEXED, section_id UNINDEXED, body
        );
    ''')
    return db


def index_revision(db: sqlite3.Connection, document_id: str, version: int,
                   lines: Iterable[str]) -> bool:
    """Commit a newer complete revision, or preserve the prior searchable text.

    Equal/older versions are skipped without consuming lines. The caller guarantees
    that a revision identifies immutable content. Empty lines input is also the
    supplied deletion operation; the revision row remains as a tombstone.
    Use a fresh connection with no open transaction. Search access is supplied by
    the caller, not implemented here; this demo is a single-tenant trusted CLI.
    """
    if version < 1:
        raise ValueError('version must be positive')
    if db.in_transaction:
        raise ValueError('Caller must finish its transaction first')
    try:
        db.execute('BEGIN IMMEDIATE')
        old = db.execute('SELECT version FROM revisions WHERE document_id=?', (document_id,)).fetchone()
        if old and old[0] >= version:
            db.rollback()
            return False
        db.execute('DELETE FROM sections WHERE document_id=?', (document_id,))
        for number, text in enumerate(lines):
            db.execute('INSERT INTO sections VALUES(?,?,?,?)', (document_id, version, number, text))
        db.execute('INSERT INTO revisions VALUES(?,?) ON CONFLICT(document_id) DO UPDATE SET version=excluded.version', (document_id, version))
        db.commit()
        return True
    except BaseException:
        db.rollback()
        raise
