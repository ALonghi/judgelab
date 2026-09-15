"""Reference checkpoint 1: persist each chunk before pulling the next."""
import sqlite3
from collections.abc import Iterable
from models import DocumentChunk
from text_tools import terms


def build_index(connection: sqlite3.Connection, chunks: Iterable[DocumentChunk]) -> int:
    count = 0
    for chunk in chunks:
        doc = chunk.document
        connection.execute("""
            INSERT INTO documents(tenant_id, document_id, title, public)
            VALUES (?, ?, ?, ?) ON CONFLICT(tenant_id, document_id) DO NOTHING
        """, (doc.tenant_id, doc.document_id, doc.title, int(doc.public)))
        connection.executemany("""
            INSERT INTO document_access VALUES (?, ?, ?)
            ON CONFLICT(tenant_id, document_id, user_id) DO NOTHING
        """, ((doc.tenant_id, doc.document_id, user) for user in doc.allowed_users))
        cursor = connection.execute(
            "INSERT INTO chunks(tenant_id, document_id, chunk_id) VALUES (?, ?, ?)",
            (doc.tenant_id, doc.document_id, chunk.chunk_id))
        chunk_pk = cursor.lastrowid
        connection.execute("INSERT INTO chunk_texts VALUES (?, ?)", (chunk_pk, chunk.text))
        title_terms, text_terms = terms(doc.title), terms(chunk.text)
        connection.executemany("INSERT INTO term_chunks VALUES (?, ?, ?, ?)",
            ((doc.tenant_id, term, chunk_pk,
              3 * (term in title_terms) + (term in text_terms))
             for term in title_terms | text_terms))
        count += 1
    return count
