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
    if event.version <= 0 or event.kind not in ("upsert", "delete"):
        raise ValueError("Invalid event version or kind")
    if event.kind == "upsert":
        document = event.document
        if not isinstance(document, Document):
            raise ValueError("Upsert requires a document")
        if (document.tenant_id, document.document_id, document.version) != (
            event.tenant_id, event.document_id, event.version
        ):
            raise ValueError("Document identity/version does not match event")
    elif event.document is not None:
        raise ValueError("Delete must not carry a document")
    key = (event.tenant_id, event.document_id)
    proposed = StoredRevision(event.version, event.document)
    previous = store.get(key)
    if previous is not None:
        if proposed.version < previous.version:
            return "ignored"
        if proposed.version == previous.version:
            if proposed == previous:
                return "ignored"
            raise ConflictingRevisionError("Same revision has different payload")
    store[key] = proposed
    return "applied"
