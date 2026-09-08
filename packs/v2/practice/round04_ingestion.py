"""Updates/deletions exercise. Read prompts/04_ingestion.md, then run:
    python -m pytest -q tests/test_04_ingestion.py -x
Suggested time: 25-35 minutes. Independent of the other rounds.
"""
from dataclasses import dataclass
from typing import Literal
from practice.models import Document


@dataclass(frozen=True)
class DocumentEvent:
    tenant_id: str
    document_id: str
    version: int  # SOURCE revision, not a local counter; strictly positive.
    kind: Literal["upsert", "delete"]
    document: Document | None = None


@dataclass(frozen=True)
class StoredRevision:
    version: int
    document: Document | None  # None = a tombstone, not absence of all history.


class ConflictingRevisionError(ValueError):
    """Same identity+source version but different payload."""


type Store = dict[tuple[str, str], StoredRevision]


def apply_event(store: Store, event: DocumentEvent) -> Literal["applied", "ignored"]:
    """Apply a source event without corrupting newer data.

    TODO:
    - Validate first, even if an event would be stale: version > 0; kind is
      upsert/delete; upsert has a Document matching identity AND version;
      delete has document=None. Invalid event -> ValueError, no mutation.
    - Identity is (tenant_id, document_id).
    - No stored revision, or strictly newer version: store the new revision
      and return "applied". A delete stores a tombstone (document=None).
    - Lower version: return "ignored" without changing anything.
    - Same version AND identical payload: return "ignored" (idempotency).
    - Same version but different payload: raise ConflictingRevisionError,
      leaving the old state untouched.
    - A stale upsert must not resurrect a deleted document. A genuinely NEWER
      upsert CAN restore it. Deletes of unseen documents also store tombstones.

    No persistence, network, threads, or batch transaction is required.
    Source versions are comparable per identity; no wall-clock assumptions.
    """
    raise NotImplementedError("Round 4: implement apply_event")
