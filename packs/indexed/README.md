# Search beyond a Python list

This pack follows the guided/full-scan search and precedes context selection.
It uses Python's standard-library SQLite driver and a local database file.
No search service, API key or downloaded model is required.

## The problem before the index

The earlier search accepts an iterable: it can receive a generator instead of a
list of every document. That avoids one source of memory growth, but its reference
implementation still accumulates matching hits before sorting. A generator also
does not avoid reading/tokenizing every document for every query.

Separate the costs:

1. Source loading: how many document bodies are held in Python at once?
2. Query work: how many records must a request examine?
3. Result buffering: do we collect every match just to return twenty?

An index addresses query work by doing reusable processing at ingestion time.
Disk-backed tables address retaining the entire index in a Python dictionary.
SQL aggregation and LIMIT address transferring every match into Python.

## Checkpoint 1: save searchable facts once

Edit `build_index.py`; run `python -m pytest -q tests/test_build.py` here.

`document_units()` turns an iterable of Documents into SearchUnits lazily. For
whole-document search, chunk_id is the empty string. Later it will identify a
piece of a document. A SearchUnit has a tenant, document ID, title, body and access
metadata. `(tenant_id, document_id, chunk_id)` is its unique identity.

For a document titled `Lease notice` with body `Notice period`, store these rows:

| Term | Unit | Weight |
|---|---|---:|
| lease | d1 | 3 |
| notice | d1 | 4 |
| period | d1 | 1 |

A **posting** records that a term occurs in a particular unit. An **inverted
index** organizes those records so a term leads to the units containing it.
The weights preserve the previous exercise's rule: 3 for title membership and
independently 1 for body membership, once per distinct term. They are not BM25.

`storage.py` provides four tables:

- `units`: integer primary key, original source identity, title, public flag.
- `contents`: the original text, separate from searchable metadata.
- `grants`: user IDs allowed to read each private unit.
- `postings`: tenant, term, unit ID and weight. Its primary key starts with
  `(tenant_id, term)`, allowing lookups for a customer's query words.

Build one unit at a time. Insert metadata first and get its generated ID from
`cursor.lastrowid`; use that ID in the other tables. `terms()` supplies normalized
sets. The union of title/body terms determines which postings exist. For each
union member, membership in the two sets determines the weight.

Python/SQL mechanics:

```python
# Related example: values are bound to placeholders, not inserted into SQL text.
connection.execute("INSERT INTO labels(name) VALUES (?)", (label,))
# The comma makes a one-item tuple. executemany also accepts an iterator of rows.
```

Use `execute` for one row and `executemany` for generated postings/grants. Write a
unit before asking for the next one. Do not first construct a corpus-sized list.
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
small candidate limit can miss a smaller useful chunk later in the corpus.

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
match most of the corpus; database cache, temporary work and disk space are real
costs. `open_index` requests a small page cache and file-backed temporary storage;
that is not a hard process-memory limit or a proof of million-document capacity.

For interviews, explain the ownership of each cost before naming a product. A
dedicated search engine may provide compressed postings, relevance models such
as BM25, optimized top-K evaluation, sharding and update tooling. None makes
permissions, corpus size, query frequency or memory budgets disappear. This pack
teaches the mechanism on a local disk-backed corpus; it is not a load benchmark.

Technical reading: [SQLite query planning](https://www.sqlite.org/queryplanner.html),
[Python SQLite API](https://docs.python.org/3/library/sqlite3.html),
[SQLite temporary storage](https://www.sqlite.org/tempfiles.html).
