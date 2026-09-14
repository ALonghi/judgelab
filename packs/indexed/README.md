# Search beyond a Python list

This pack follows the guided/full-scan search and precedes context selection.
It uses Python's standard-library SQLite driver and a local database file.
No search service, API key or downloaded model is required.

## Why the existing search slows down

The earlier search opens every document and splits its text into words for every
query. Reading one document at a time keeps Python from holding the entire
collection, but it does not reduce the work repeated by each search. Collecting
and sorting every match creates a separate memory cost.

## Choose the production approach

Full-text search is the feature: find documents by words in their text. An
inverted index is a common way to implement that feature: each word points to the
documents containing it. They are not competing alternatives.

For a new system, estimate document volume, search frequency and how quickly
updates must appear. For an existing system, measure which part is slow. Then
choose the smallest option that meets the requirement:

| Option | Use it when | Main cost |
|---|---|---|
| Scan stored documents | Searches are rare or measurements show the scan is fast enough. | Every search reads all searchable text. Read in batches to bound application memory. |
| Database full-text search | Repeated keyword searches need an index, and the existing database handles the measured load. | The database maintains the word lookup and ranking. |
| Separate search service | Search load harms the primary database, or the product needs behavior it cannot provide, such as typo tolerance or language-specific analysis. | Another service must receive every document, permission change and deletion. It can be temporarily stale. |

SQLite FTS5 and PostgreSQL text search are examples of the second option.
Dedicated engines implement the third. Both usually maintain an inverted index
internally and store it more compactly than ordinary application rows.

## What this exercise implements

This pack writes the inverted index as normal SQLite rows so its mechanics are
visible. One row records a word, a document or chunk ID, and that word’s score
contribution. The exercise calls this row a **posting**. This schema is a learning
tool, not a recommendation for a million-file deployment.

A 10,000-word document containing 2,000 distinct normalized words creates 2,000
posting rows here. One million documents with that average would create two
billion rows. A database full-text index or dedicated engine uses specialized,
compressed storage instead of this row-per-word representation.

The other tables separate searchable identity, body text and user permissions so
their roles remain visible. A production schema may keep title and body together
and let its database or search engine maintain the text index internally.

## How changes reach the index

Indexing normally runs when a file is uploaded or changed, after text extraction.
It does not rebuild on ordinary application startup. The work can run in the
upload transaction when changes must be searchable immediately, or in a
background worker when a short delay is acceptable.

An update replaces that document’s old index entries. A deletion removes them.
A full rebuild is useful when the word-splitting rules change or the index must be
repaired. This checkpoint implements initial construction from unique documents;
it does not implement uploads, updates, deletions, workers or rebuilds.

## Checkpoint 1: save searchable facts once

Edit `build_index.py`; run `python -m pytest -q tests/test_build.py` here.

`document_units()` turns an iterable of Documents into SearchUnits lazily. For
whole-document search, chunk_id is the empty string. Later it will identify a
piece of a document. A SearchUnit has a tenant, document ID, title, body and access
metadata. `(tenant_id, document_id, chunk_id)` is its unique identity.

The previous search checked every document's words for every query. Save those
checks at import time: one row says which word occurs in which unit, plus the
points that word contributes if someone searches for it. This row is a **posting**.
The word itself is stored as text; you do not need a separate word-ID table.

`open_index()` in `storage.py` already creates four tables. Your function inserts
rows into them:

- `units`: integer primary key `id`, tenant/document/chunk identity, title, public flag.
- `contents`: `unit_id` and the original body `text`.
- `grants`: `unit_id` and `user_id`, one row per allowed user.
- `postings`: `tenant_id`, `term`, `unit_id` and `weight`.

For tenant `firm-a`, insert document `d1`, title `Lease notice`, body `Notice
period`. Suppose SQLite assigns `units.id = 7`. The source ID remains `d1`;
`unit_id = 7` links the other tables' rows to that source record. Obtain this
integer from the insert cursor's `lastrowid`, rather than inventing an ID.

`terms(title)` gives `{"lease", "notice"}`; `terms(body)` gives `{"notice",
"period"}`. Their union contains three distinct words, so insert three postings:

| tenant_id | term | unit_id | weight |
|---|---|---:|---:|
| firm-a | lease | 7 | 3 |
| firm-a | notice | 7 | 4 |
| firm-a | period | 7 | 1 |

`weight` is a score contribution. Title membership contributes 3 and body
membership independently contributes 1. Thus notice earns 4. It is neither a
word position nor an occurrence count; repeating notice in the body adds nothing.
This preserves the earlier exercise's scoring rule, rather than implementing BM25.

A second document `d2`, title `Schedule`, body `Period`, receives `units.id = 8`.
Its postings are `(firm-a, schedule, 8, 3)` and `(firm-a, period, 8, 1)`.
There are two rows for period because two documents contain it.

For a later query `lease period`, assuming both documents are readable, select
rows for those two words in firm-a. Unit 7 contributes 3 + 1 = 4; unit 8
contributes 1. The notice and schedule rows do not match this query. Group by
unit_id and sum the matching weights, then join to units to recover document IDs
and titles. The stored bodies are not needed to compute these scores.

This is an **inverted index**: start with a word and look up the documents
containing it. SQLite's supplied primary-key index on
`(tenant_id, term, unit_id)` supports that lookup. Storing a table of words alone
would not avoid scanning it without a suitable database index. Common words can
still match many rows.

In this checkpoint, implement only the builder. For each incoming unit, insert
metadata, get its database ID, write its body and grants, and compute its postings
from the union of the two term sets. Finish these writes before requesting the
next unit. Retain only the current unit's sets and a unit counter in Python.
A unit with no terms still needs metadata, body and grants and counts as one;
empty input returns zero. The next checkpoint implements the query.

Python/SQL mechanics:

```python
# Related example: values are bound to placeholders, not inserted into SQL text.
connection.execute("INSERT INTO labels(name) VALUES (?)", (label,))
# The comma makes a one-item tuple. executemany also accepts an iterator of rows.
```

Use `execute` for one row and `executemany` for generated postings/grants. Write a
unit before asking for the next one. Do not first construct a list of the entire document collection.
The caller owns commit/rollback; `with connection:` commits on success or rolls
back on an exception. It does not close the connection.

The initialized index may already contain different identities. This checkpoint
appends unique units; duplicate identities are invalid and updates/deletes are
outside its contract. A real indexing pipeline needs a revision-aware update
policy and bounded commit batches. One huge transaction has its own costs.

## Checkpoint 2: score using the stored postings

Edit `search_index.py`; run `python -m pytest -q tests/test_query.py`.
Tests seed explicit posting weights, so you can practise this before your builder
passes. In the complete pipeline, the previous checkpoint creates those rows.

For query `lease period`, read only those two terms' posting lists in the requested
tenant. d1 earns 3+1=4. A different unit containing only `period` earns 1. No stored
document body needs to be read to calculate these scores.

Use SQL operations in this order:

1. Bind the tenant and distinct normalized query terms in the posting lookup.
2. Join each posting to `units` using its unit ID. Enforce tenant and access:
   public within that tenant, or an `EXISTS` check for this user in `grants`.
3. `GROUP BY` unit ID and `SUM` its matching posting weights.
4. `ORDER BY` score descending, then document ID and chunk ID ascending.
5. Apply `LIMIT` in SQL and convert only those rows to IndexedHit records.

`JOIN` associates rows by an ID. `GROUP BY` collects matching rows for the same
unit so `SUM` computes one score. `EXISTS` answers whether a grant row exists;
joining every grant directly could multiply scoring rows for users with several
grants. Distinct query terms likewise prevent repetition inflating scores.

Related aggregation syntax, using unrelated data:

```sql
SELECT account_id, SUM(amount) AS total
FROM payments
WHERE currency = ?
GROUP BY account_id
ORDER BY total DESC, account_id ASC
LIMIT ?
```

For an IN clause with several query terms, generate only the `?, ?, ...`
placeholder syntax. Pass the actual strings as execute parameters. Never format
tenant IDs, usernames or query strings into SQL. Inputs contain at most 32 unique
query terms here; very large query expansion needs another parameter strategy.

Validate limit in 1..100 before returning for an empty query. Query terms are OR
matches. Do not read `contents`, do not mutate the database, and fetch at most
limit rows into Python. There is intentionally no category filter in this pack.

Inspect the plan by running `EXPLAIN QUERY PLAN` on your SELECT with the same
parameters. A posting lookup should search on tenant and term. A scan of every
body, or a Python sort of all hits, defeats the point even if small tests return
the expected scores. The tests inspect both result transfer and indexed lookup.

## Checkpoint 3: change the unit from a file to a chunk

Edit `chunk_documents.py`; run `python -m pytest -q tests/test_chunks.py`.

A relevant file can be too long to send to a model. Yield SearchUnits containing
at most max_words whitespace-delimited words, preserving case and punctuation.
Use `re.finditer(r"\S+", document.text)` and a small list of pending words;
`text.split()` allocates every word of the document at once. Yield whenever that
list fills and flush a final short list. Skip empty bodies and restart chunk IDs
at `"0"` for each document. Copy source identity, title and access metadata.

Fixed word windows are a transparent baseline. They can cut sentences or separate
evidence, and editing a document can shift every subsequent chunk ID. Production
systems may use section/sentence boundaries, overlap, source offsets and versions.
Those policies must be defined rather than assumed.

Use the same builder and query for chunk units. Title weight is repeated for each
chunk from that document; a title-only match can therefore return several chunks
with weak body evidence. Evaluate this limitation before using the scoring rule.

`load_chunks(connection, hits, tenant_id=..., user_id=...)` is provided. It loads
only the returned units' text, preserves rank order and rechecks access. Its Chunk
fields match the next exercise's input. `build_context()` then applies its word
budget and per-document cap. Search limit and context budget are distinct: a
small candidate limit can miss a smaller useful chunk later in the document collection.

## Try the completed pipeline

After implementing all three checkpoints, run `python demo.py`. The demo creates
a temporary on-disk index, prints whole-document scores, then rebuilds a separate
chunk index and prints ranked chunks ready for `build_context`. It deliberately
does not select context or make a model call.

## Memory and scale: what this does and does not establish

Index construction retains one SearchUnit and its term sets in Python, plus the
database's buffers. Chunking retains one source Document string and a bounded
word buffer. This is not a streaming PDF parser; an enormous single document or
word can still be expensive.

At query time Python receives at most K small metadata records. SQLite still
examines matching postings and performs grouping/sorting. Frequent words can
match most of the document collection; database cache, temporary work and disk space are real
costs. `open_index` requests a small page cache and file-backed temporary storage;
that is not a hard process-memory limit or a proof of million-document capacity.

For interviews, explain the ownership of each cost before naming a product. A
dedicated search engine may provide compressed postings, relevance models such
as BM25, optimized top-K evaluation, sharding and update tooling. None makes
permissions, document collection size, query frequency or memory budgets disappear. This pack
teaches the mechanism on a local disk-backed document collection; it is not a load benchmark.

Technical reading: [SQLite query planning](https://www.sqlite.org/queryplanner.html),
[Python SQLite API](https://docs.python.org/3/library/sqlite3.html),
[SQLite temporary storage](https://www.sqlite.org/tempfiles.html).

Further reading: [FTS5 storage and updates](https://www.sqlite.org/fts5.html),
[Elasticsearch refresh semantics](https://www.elastic.co/docs/manage-data/data-store/near-real-time-search).

[PostgreSQL full-text indexes](https://www.postgresql.org/docs/current/textsearch-indexes.html) describe its built-in inverted index option.
