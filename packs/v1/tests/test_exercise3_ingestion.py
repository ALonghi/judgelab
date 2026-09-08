from practice.exercise3_ingestion import (
    IncomingDocument,
    InMemoryDocumentStore,
    ingest_documents,
)


def test_first_ingestion_creates_version_one():
    store = InMemoryDocumentStore()
    ingest_documents(
        store,
        [IncomingDocument("t1", "doc-1", "hello", "dms")],
    )

    doc = store.get("t1", "doc-1")
    assert doc is not None
    assert doc.content == "hello"
    assert doc.version == 1


def test_reingesting_identical_document_is_noop():
    store = InMemoryDocumentStore()
    incoming = IncomingDocument("t1", "doc-1", "hello", "dms")

    ingest_documents(store, [incoming])
    ingest_documents(store, [incoming])

    assert store.get("t1", "doc-1").version == 1
    assert len(store.all()) == 1


def test_changed_document_updates_and_increments_version():
    store = InMemoryDocumentStore()

    ingest_documents(
        store,
        [IncomingDocument("t1", "doc-1", "v1", "dms")],
    )
    ingest_documents(
        store,
        [IncomingDocument("t1", "doc-1", "v2", "dms")],
    )

    doc = store.get("t1", "doc-1")
    assert doc.content == "v2"
    assert doc.version == 2


def test_identity_is_tenant_scoped():
    store = InMemoryDocumentStore()

    ingest_documents(
        store,
        [
            IncomingDocument("firm-a", "42", "A", "dms"),
            IncomingDocument("firm-b", "42", "B", "dms"),
        ],
    )

    assert len(store.all()) == 2
    assert store.get("firm-a", "42").content == "A"
    assert store.get("firm-b", "42").content == "B"


def test_duplicate_identity_in_same_batch_is_processed_in_order():
    store = InMemoryDocumentStore()

    ingest_documents(
        store,
        [
            IncomingDocument("t1", "doc-1", "v1", "dms"),
            IncomingDocument("t1", "doc-1", "v2", "dms"),
            IncomingDocument("t1", "doc-1", "v2", "dms"),
            IncomingDocument("t1", "doc-1", "v3", "email"),
        ],
    )

    doc = store.get("t1", "doc-1")
    assert doc.content == "v3"
    assert doc.source == "email"
    assert doc.version == 3
