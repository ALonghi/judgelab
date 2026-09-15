"""Checkpoint 1. Read README.md. Schema and extracted chunks are supplied."""
import sqlite3
from collections.abc import Iterable
from models import DocumentChunk
from text_tools import terms


def build_index(connection: sqlite3.Connection, chunks: Iterable[DocumentChunk]) -> int:
    """Append extracted chunks to SQLite and return the number written.

    Input comes from an ingestion pipeline, one bounded DocumentChunk at a time.
    chunk.document is shared metadata, never a complete file body. Metadata for
    the same (tenant_id, document_id) is consistent, including existing rows.
    Store document title/public in documents and users in document_access once.
    Store each chunk in chunks and its original text in chunk_texts.
    Write one term_chunks row per distinct term in title OR chunk text:
    weight = 3 for title, independently +1 for text. Use terms(); repetition
    adds nothing. The row key is (tenant_id, term, chunk_pk); chunk_pk = chunks.id.
    Title boosts still apply to every chunk; this is the toy 3/1 scoring rule.
    Chunk IDs are nonempty, unique within their tenant/document, and absent
    from the database. Store chunks even when title/text contain no tokens.
    Write each chunk BEFORE requesting the next. Keep only current chunk term
    sets and metadata; do not retain the entire input or a set of all documents.
    INSERT ... ON CONFLICT DO NOTHING can reuse document/access rows on disk.
    Do not mutate input or commit/rollback/close; the caller owns the transaction.
    Duplicate chunks may raise sqlite3.IntegrityError. Updates, deletes and
    conflicting document metadata are outside this initial-ingestion contract.
    """
    raise NotImplementedError("Store chunks and their term lookup rows")
