"""Synthetic source metadata, streaming input and retrieval records."""
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    """Metadata only: the file body is never required in this record."""
    tenant_id: str
    document_id: str
    title: str
    public: bool = False
    allowed_users: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ExtractedDocument:
    """Metadata and a one-pass stream of whitespace-delimited source words."""
    document: Document
    words: Iterable[str]


@dataclass(frozen=True)
class DocumentChunk:
    """A bounded piece of text referring to shared document metadata."""
    document: Document
    chunk_id: str
    text: str


@dataclass(frozen=True)
class IndexedHit:
    tenant_id: str
    document_id: str
    chunk_id: str
    title: str
    score: int


@dataclass(frozen=True)
class Chunk:
    """Retrieved text with caller-scoped access for the context exercise."""
    tenant_id: str
    document_id: str
    chunk_id: str
    text: str
    allowed_users: frozenset[str] = frozenset()
    public: bool = False
