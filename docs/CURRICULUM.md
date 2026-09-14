# Curriculum order

The path starts with small Python transformations, then puts an HTTP boundary
around supplied document data. Ingestion establishes where document state comes
from before search introduces derived indexes. Concurrency and cancellation come
before batch uploads. Architecture discussions revisit the implemented mechanisms
and extend them to production workloads.

`app/catalog.json` is the executable order. Home selects the first unfinished
required activity. Continue selects the next unfinished required activity after
the current one, then returns to earlier unfinished work if necessary. Both skip
optional recaps. With all required work complete, the review action starts again
at the first activity. Direct links remain available throughout; prerequisites
provide guidance rather than locking activities.

## 1. Python data handling — 3 activities

1. `q-sets`: distinct words and set membership.
2. `c-latest`: select the latest record for each identity.
3. `c-counts`: aggregate document category counts.

Sets and dictionaries are introduced before the learner needs them in repository
logic. The two coding warm-ups share their original file, so existing work stays
intact and each activity still validates its own selected functions.

## 2. APIs & document state — 4 activities

1. `p-fastapi`: validate HTTP inputs and enforce tenant scope below the route.
2. `p-ingest`: make repeated imports idempotent using local version counters.
3. `q-version`: distinguish local counters from source-assigned revisions.
4. `c-events`: handle stale source events, conflicts and deletion tombstones.

This establishes the request boundary and document write path before implementing
ranked retrieval. FastAPI uses a simple substring repository; it does not require
the later ranking helpers or index. The version quiz bridges two deliberately
different ingestion contracts instead of letting their semantics blur together.

## 3. Search rules & access — 8 activities

1. `q-score`: check the title/body scoring rule.
2. `g-score`: implement scoring.
3. `q-tenants`: check tenant and user access rules.
4. `g-permissions`: implement access checks.
5. `q-filter`: distinguish no category restriction from an empty selection.
6. `g-categories`: implement category matching.
7. `q-limit`: understand why access filtering precedes ranking and limiting.
8. `g-search`: combine the helpers into complete ranked search.

Each check now immediately precedes the code that uses it. The four coding
checkpoints still share their original workspace. The final checkpoint validates
the helpers and integration together.

## 4. Indexes, full-text search & context — 6 required activities

1. `c-index-build`: persist per-term weights rather than rereading files per query.
2. `c-index-query`: query stored weights and apply the result limit in SQL.
3. `c-fts`: use SQLite's maintained full-text index and ranking.
4. `c-chunking`: create identified text sections that can be retrieved.
5. `q-context`: check how a context budget changes passage selection.
6. `c-context`: select permitted evidence while preserving citations.

`c-search` remains an optional independent recap of guided search, displayed
separately and excluded from chapter numbering and automatic continuation.

The manual index exposes storage and query mechanics, then FTS5 replaces those
hand-built internals. Chunking and context use already-ranked text. Full-document
bodies are still loaded by the indexed pack; the later upload extractor addresses
bounded input for its narrower UTF-8 line contract.

## 5. Reliability & async lab — 6 activities

1. `a-refactor`: fix blocked scheduling and shared default state.
2. `a-fetch`: bound concurrent calls and deduplicate metadata lookups.
3. `q-cancel`: check cancellation and ownership of unfinished work.
4. `a-federated`: combine unreliable retrieval sources with partial outcomes.
5. `a-parser`: parse messages across arbitrary network chunk boundaries.
6. `a-llm`: handle stream failures and safe provider fallback.

Basic concurrency and cancellation precede composition of multiple sources.
The final pair practises incremental input and partial-output semantics. Parsing
NDJSON is not a requirement of the fallback exercise; they retain separate
contracts.

## 6. Large uploads & searchable files — 3 activities

1. `u-upload`: transfer bounded byte ranges and resume acknowledged progress.
2. `u-batch`: bound allocated tasks and active uploads, retain per-file outcomes,
   and clean up on cancellation.
3. `u-extract`: decode UTF-8 incrementally and emit bounded text lines.

Batching builds on the earlier concurrency and cancellation work. Extraction
connects stored originals to the supplied SQLite FTS5 revision demo, using the
revision and search concepts already introduced. Byte upload parts and searchable
text sections remain distinct. PDF/OCR, durable jobs and cloud multipart protocols
are architecture topics, not hidden coding requirements.

## 7. Think beyond the function — 6 discussions

1. `s-api`: separate HTTP, policy and storage responsibilities.
2. `s-ingestion`: recover the gap between saving state and notifying workers.
3. `s-large-import`: design large uploads and full-text search for millions of
   files per tenant, allowing delayed additions but prompt access revocation.
4. `s-search`: choose indexes, access enforcement and scaling based on workload.
5. `s-latency`: reason about deadlines, partial results and capacity limits.
6. `s-chat`: assemble verifiable answers from permitted evidence.

Start with component ownership, follow writes through ingestion and large imports,
then examine query scaling, latency and downstream answer construction. The
large-import discussion explicitly builds on durable ingestion. These activities
use self-review rubrics; automated keyword cues do not establish correctness.

## Checks that protect this order

- `tests_app/test_curriculum.py` verifies the complete sequence, chapter membership
  and that each prerequisite is earlier and required.
- `tests_ui/lesson_views.test.cjs` exercises the real home renderer and walks
  Continue across every chapter boundary, including saved completion and recaps.
- Existing acceptance suites still validate the same learner files and functions.
  Reordering changes neither activity IDs nor workspace paths.
