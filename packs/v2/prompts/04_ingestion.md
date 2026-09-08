# Round 4 — reliable ingestion with source revisions and deletions

**Timebox: 25–35 minutes.** Implement `practice/round04_ingestion.py`.
Run `python -m pytest -q tests/test_04_ingestion.py -x`.

A connector sends document events. They may arrive late or be redelivered. Build a
small in-memory state updater. Identity is `(tenant_id, document_id)`; version is a
monotonically increasing revision supplied by the source **per identity**.

## Step 1: inserts, updates, and retries

`apply_event(store, event)` returns `"applied"` for a missing or newer source
revision and `"ignored"` for an older revision or exact duplicate. Store the source
version itself, not a count of how often your function was called.

At the same version, a different payload is a conflict: raise
`ConflictingRevisionError` and leave state unchanged. Unlike Round 1's warm-up,
you must not silently pick whichever conflicting event arrived last.

## Step 2: deletions

A delete stores `StoredRevision(version, None)`: a tombstone preserving knowledge
of the last source version. A delete for an unknown identity also stores a tombstone.

Sequence: upsert v1 -> delete v5 -> upsert v3. The final state must stay deleted at
v5. Sequence: delete v5 -> upsert v6. The final state is live at v6.

## Step 3: invalid inputs

Validate before deciding whether an event is stale. version must be positive.
kind must be upsert/delete. Upsert must contain a Document with matching tenant,
ID, and version; delete must have no document payload. Raise ValueError without
mutating the store on any invalid input. These rules are fully enumerated in tests.

## Architecture follow-up

Your code currently runs in a single process. What would make the update atomic
in a database? How do workers avoid overwriting newer revisions? How do embedding
and search-index jobs detect stale work? What is the failure between committing a
new revision and publishing its indexing job? When is it safe to discard a tombstone?

Do not implement queues/transactions here. Explain the boundary and the invariant.
