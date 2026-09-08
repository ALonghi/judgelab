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


def ingest_documents(store: InMemoryDocumentStore,
                     documents: list[IncomingDocument]) -> None:
    for incoming in documents:
        key = (incoming.tenant_id, incoming.external_id)
        previous = store.get(*key)
        if previous is not None and (previous.content, previous.source) == (incoming.content, incoming.source):
            continue
        version = 1 if previous is None else previous.version + 1
        store._documents[key] = StoredDocument(
            incoming.tenant_id, incoming.external_id, incoming.content, incoming.source, version
        )
