"""Synthetic records shared by the disk-backed search exercises."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    tenant_id: str
    document_id: str
    title: str
    text: str
    public: bool = False
    allowed_users: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SearchUnit:
    tenant_id: str
    document_id: str
    chunk_id: str  # "" for a whole document; otherwise a chunk identity.
    title: str
    text: str
    public: bool = False
    allowed_users: frozenset[str] = frozenset()


@dataclass(frozen=True)
class IndexedHit:
    tenant_id: str
    document_id: str
    chunk_id: str
    title: str
    score: int


@dataclass(frozen=True)
class Chunk:
    tenant_id: str
    document_id: str
    chunk_id: str
    text: str
    allowed_users: frozenset[str] = frozenset()
    public: bool = False
