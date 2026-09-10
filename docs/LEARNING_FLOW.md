# Learning-flow review: scoring through retrieval

## The gap that was corrected

The previous path introduced ranked context before teaching where ranked chunks
came from. It also jumped from a small full scan to a discussion about millions
of documents without an executable indexing step. Definitions and headings did
not close that implementation gap.

## Current sequence and handoffs

| Activities | What the learner implements or checks | Handoff and limit |
|---|---|---|
| q-sets, q-score, q-tenants, q-filter, q-limit | Unique words, per-field points, eligibility and ordering | Small examples; no scalable retrieval claim |
| g-score, g-permissions, g-categories, g-search | The four parts of a simple search | A full-scan correctness baseline; iterable input does not bound all hit storage |
| c-latest, c-counts, c-search | Identity/version selection, aggregation and independent search rehearsal | Exact input contracts differ intentionally; indexed exercises accept unique units |
| c-index-build | Write metadata, text, access grants and weighted postings incrementally to SQLite | Durable term-to-unit lookup; no updates or deletion policy yet |
| c-index-query | Match postings, check access, sum weights, order and limit in SQL | Top eligible IDs/titles/scores; no body reads during scoring |
| c-chunking | Yield bounded text units with parent IDs and access metadata | Same index can score chunks; load_chunks fetches returned text in rank order |
| q-context, c-context | Keep whole chunks under a budget and construct citations | Word budget is a toy proxy; search limit and context capacity are different limits |
| q-version, c-events | Recognize stale revisions and preserve deletion history | Needed to design updates to derived indexes; the initial index pack itself is append-only |
| a-refactor, a-fetch, q-cancel, a-federated | Async mechanics, bounded calls, ownership, partial results and score merging | Fakes have comparable scores; real sources need an explicit merge policy |
| a-parser, a-llm | Message boundaries and streamed-output failure handling | Transport pieces and retrieved text chunks are different units |
| p-fastapi, p-ingest | HTTP adapter and local-change ingestion variant | V1 substring matching/local versions intentionally differ from V2 |
| s-search, s-ingestion, s-chat, s-latency, s-api | Discuss scale, recoverability, evidence, deadlines and boundaries | Design arguments build on executable mechanisms, not a claim of production completeness |

All activities use distinct Problem, Walkthrough, Practice and Knowledge base
views. Problem contains the interview-facing scenario, fixed requirements and
deliverable. Walkthrough retains concrete examples and operations. Definitions,
SQL/Python notes, design alternatives and related lessons belong in Knowledge base,
not in the interview dialogue. New indexed lessons explain the SQL operations,
table keys, scoring arithmetic, transaction owner, data movement and output.
Their tests are independent, so an unfinished earlier checkpoint does not cause
unrelated import failures. A separate integration check combines the reference
checkpoints with the existing context builder and checks source IDs and access.

## What remains deliberately out of scope

- BM25 implementation, embedding models and neural rerankers. These are named as
  further retrieval choices; the new index preserves the existing 3:1 scoring.
- Production PDF extraction, arbitrary-size single-document streaming, index
  sharding, load tests and capacity planning. No claim that SQLite makes every
  million-document workload safe or fast.
- Category filtering in the indexed pack. Tenant and per-user access are tested;
  this simplified SQL contract is not a drop-in replacement for every V2 feature.
- Incremental index updates and tombstone retention. The event lessons provide
  reasoning for a future extension; the new builder accepts unique units.

The distinction matters in an interview: explain where memory grows, which work
is repeated, and which storage/query mechanism changes each cost. Returning K
rows limits application result storage, but frequent-term postings and database
aggregation can still be expensive.
