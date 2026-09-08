from dataclasses import replace
import pytest
from practice.models import Document
from practice.round04_ingestion import DocumentEvent, StoredRevision, ConflictingRevisionError, apply_event


def upsert(version=1, text="body", *, tenant="a", key="1"):
    doc = Document(tenant, key, version, "Title", text, public=True)
    return DocumentEvent(tenant, key, version, "upsert", doc)


def delete(version=2, *, tenant="a", key="1"):
    return DocumentEvent(tenant, key, version, "delete")


def test_ingestion_first_insert_and_source_version_not_local_counter():
    store = {}
    event = upsert(version=7)
    assert apply_event(store, event) == "applied"
    assert store == {("a", "1"): StoredRevision(7, event.document)}


def test_ingestion_duplicate_is_noop():
    store = {}
    event = upsert()
    apply_event(store, event)
    before = dict(store)
    assert apply_event(store, event) == "ignored"
    assert store == before


def test_ingestion_newer_update_and_stale_update():
    store = {}
    apply_event(store, upsert(1))
    newest = upsert(5, "new")
    assert apply_event(store, newest) == "applied"
    assert apply_event(store, upsert(3, "stale")) == "ignored"
    assert store[("a", "1")] == StoredRevision(5, newest.document)


def test_ingestion_delete_tombstone_prevents_stale_resurrection():
    store = {}
    apply_event(store, upsert(1))
    assert apply_event(store, delete(4)) == "applied"
    assert apply_event(store, upsert(2)) == "ignored"
    assert store[("a", "1")] == StoredRevision(4, None)


def test_ingestion_delete_unseen_then_duplicate_delete():
    store = {}
    assert apply_event(store, delete(10)) == "applied"
    assert apply_event(store, delete(10)) == "ignored"
    assert apply_event(store, upsert(9)) == "ignored"
    assert store[("a", "1")] == StoredRevision(10, None)


def test_ingestion_newer_upsert_can_restore_deleted():
    store = {}
    apply_event(store, delete(4))
    assert apply_event(store, upsert(5, "restored")) == "applied"
    assert store[("a", "1")].document.text == "restored"


def test_ingestion_identity_includes_tenant():
    store = {}
    apply_event(store, upsert(1, "A"))
    apply_event(store, upsert(1, "B", tenant="b"))
    assert len(store) == 2
    assert store[("b", "1")].document.text == "B"


@pytest.mark.parametrize("conflict", [upsert(2, "different"), delete(2)])
def test_ingestion_conflicting_same_revision_does_not_mutate(conflict):
    store = {}
    apply_event(store, upsert(2, "original"))
    before = dict(store)
    with pytest.raises(ConflictingRevisionError):
        apply_event(store, conflict)
    assert store == before


@pytest.mark.parametrize("bad", [
    upsert(0), delete(-1), DocumentEvent("a", "1", 1, "other"),
    DocumentEvent("a", "1", 1, "upsert"),
    DocumentEvent("a", "1", 1, "delete", upsert().document),
    DocumentEvent("a", "1", 1, "upsert", upsert(2).document),
    DocumentEvent("a", "1", 1, "upsert", upsert(1, tenant="b").document),
    DocumentEvent("a", "1", 1, "upsert", upsert(1, key="other").document),
])
def test_ingestion_invalid_event_rejected_even_if_older(bad):
    store = {("a", "1"): StoredRevision(100, None)}
    before = dict(store)
    with pytest.raises(ValueError):
        apply_event(store, bad)
    assert store == before
