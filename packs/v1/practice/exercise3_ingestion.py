from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IncomingDocument:
    tenant_id: str
    external_id: str
    content: str
    source: str


@dataclass
class StoredDocument:
    tenant_id: str
    external_id: str
    content: str
    source: str
    version: int


class InMemoryDocumentStore:
    def __init__(self) -> None:
        # You may change the internal representation.
        self._documents: dict[tuple[str, str], StoredDocument] = {}

    def get(self, tenant_id: str, external_id: str) -> StoredDocument | None:
        return self._documents.get((tenant_id, external_id))

    def all(self) -> list[StoredDocument]:
        return list(self._documents.values())


def ingest_documents(
    store: InMemoryDocumentStore,
    documents: list[IncomingDocument],
) -> None:
    """
    Exercise 3: idempotent document ingestion.

    Identity
    --------
    A document is uniquely identified by:
        (tenant_id, external_id)

    Requirements
    ------------
    1. First ingestion creates the document with version=1.
    2. Re-ingesting identical content/source is a no-op:
       version must NOT increase.
    3. If content OR source changes, update the existing document and increment
       version by exactly 1.
    4. Same external_id in different tenants represents two independent docs.
    5. If the same identity appears multiple times in one input batch, process
       it in input order. The final stored state should reflect the final item.

    Keep it simple. This is an in-memory exercise.

    Interview follow-ups
    --------------------
    - Translate this to PostgreSQL. What UNIQUE constraint would you use?
    - Would SELECT-then-INSERT be race safe?
    - How would INSERT ... ON CONFLICT help?
    - Where would you draw the transaction boundary for a batch?
    - If ingestion triggers embedding/indexing, how would you make that side
      effect idempotent too?
    - What happens when two workers ingest updates concurrently?
    """
    raise NotImplementedError("Implement exercise 3")
