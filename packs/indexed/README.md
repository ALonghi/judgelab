# Index extracted chunks, then search them

This pack follows full-scan search and connects disk-backed retrieval to context
selection. It uses Python's SQLite driver, local files and synthetic data.

## Start with the input and its source

An ingestion pipeline reads a file incrementally, extracts words, groups them into
bounded chunks and feeds those chunks to the index builder. Searches later read
the saved term lookup. They do not reopen every file.

| Stage | Input | Output |
|---|---|---|
| Supplied `iter_words` | An open decoded plain-text stream | Words read in bounded blocks |
| `chunk_documents` | `ExtractedDocument(document, words)` records | An iterator of `DocumentChunk` records |
| `build_index` | An open SQLite connection and those chunks | Stored document metadata, chunk text and term lookup rows |
| `search_index` | Existing index, query, trusted tenant/user and limit | Ranked `IndexedHit` records |
| Supplied `load_chunks` | Ranked hits and caller access | Selected text with source identity for `build_context` |

You learn the builder and query first with supplied chunks, then implement their
upstream chunker. All three checkpoints operate on chunks. None requires a
complete source body string. `Document` holds only metadata; `DocumentChunk`
refers to it through its `document` field. Two chunks from one file share that
metadata object rather than copying its title and users into separate fields.

The reader takes decoded plain text, calls `read(read_chars)` (default 4096), and
preserves partial words across reads. It rejects words exceeding `max_word_chars`
(default 1024). The chunker buffers at most `max_words` words. These explicit bounds
make text buffering independent of total file size. A custom upstream extractor
must supply bounded words too. Title size and access-list size are separate
metadata costs. PDF/OCR parsers and sentence-aware boundaries are not supplied.

## Choose the storage approach

Full-text search is the feature. An inverted index is a lookup from a word to the
records containing it. An entry in that lookup is conventionally called a
**posting**. Here the table is named `term_chunks`: each row links a term to a
chunk and records its score contribution.

| Approach | A reason to choose it | Main cost |
|---|---|---|
| Scan documents | Infrequent searches over a small collection meet the target. | Repeated text reads and scoring on every query. |
| Database full-text search | Repeated keyword queries fit the existing database's measured capacity. | The database maintains an index and computes ranking. |
| Separate search service | Search needs independent capacity or features the primary database lacks. | Another store must receive edits, deletion and access changes. |

This exercise uses ordinary SQLite rows to expose the word-to-chunk mechanism.
Real full-text engines have specialized index storage. Millions of chunks can
produce very many term rows; this schema is not a capacity benchmark. A SQL LIMIT
bounds final result transfer, not all database work.

## Follow the five tables

Document `firm-a/d1` has title `Lease notice`, is private and is shared with
`reader-a`. The ingestion pipeline produces chunk `0`: `Notice period` and chunk
`1`: `Thirty days`. The complete file body is not an input field.

### Document metadata, stored once

`documents` is keyed by `(tenant_id, document_id)`:

| tenant_id | document_id | title | public |
|---|---|---|---|
| firm-a | d1 | Lease notice | 0 |

`document_access` contains one row per allowed user per document:

| tenant_id | document_id | user_id |
|---|---|---|
| firm-a | d1 | reader-a |

### Chunk identity and text

`chunks` refers to its document through `(tenant_id, document_id)`. Its generated
integer `id` is distinct from the source `chunk_id`, which is nonempty and unique
within a document. Suppose SQLite assigns IDs 7 and 8:

| id | tenant_id | document_id | chunk_id |
|---|---|---|---|
| 7 | firm-a | d1 | 0 |
| 8 | firm-a | d1 | 1 |

`chunk_texts` uses `chunk_pk = chunks.id`:

| chunk_pk | text |
|---|---|
| 7 | Notice period |
| 8 | Thirty days |

Keeping text separate lets the query score and return IDs before loading text.

### Term-to-chunk lookup

Use `terms()` to find distinct normalized title/text words. A term contributes
3 if it belongs to the document title and independently 1 if it belongs to this
chunk's text. Repeated occurrences do not add points.

| tenant_id | term | chunk_pk | weight |
|---|---|---|---|
| firm-a | lease | 7 | 3 |
| firm-a | notice | 7 | 4 |
| firm-a | period | 7 | 1 |
| firm-a | lease | 8 | 3 |
| firm-a | notice | 8 | 3 |
| firm-a | thirty | 8 | 1 |
| firm-a | days | 8 | 1 |

The primary key `(tenant_id, term, chunk_pk)` supports looking up a tenant and word.
`chunk_pk` links each match back to its chunk. A composite foreign key also prevents
linking a term row to a different tenant's chunk.

A query for `lease period` gives chunk 0 a score of 4 and chunk 1 a score of 3.
Join their document metadata to get the title and check access. No chunk text is
needed to calculate those scores.

The title is stored once, but its scoring signal still applies to every chunk.
A title-only match can therefore return many chunks with little useful body
text. This preserves the earlier toy 3/1 score; it is not BM25 or a validated
ranking policy. Body-based reranking and a per-document result cap are possible
extensions with different effects on relevance.

## Checkpoint 1: persist each extracted chunk

Edit `build_index.py`; run `python -m pytest -q tests/test_build.py` here.

Input: `chunks`, an iterable of `DocumentChunk(document, chunk_id, text)` supplied
by ingestion. Tests supply small chunks directly, independently of your chunker.
The schema is already created by `open_index()`.

For each chunk:

1. Store its document's title/public and allowed users once. Use database
   uniqueness and `ON CONFLICT ... DO NOTHING` to reuse document/access rows.
2. Insert its chunk identity, obtain `cursor.lastrowid`, and write its original
   text to `chunk_texts` using that ID as `chunk_pk`.
3. Compute the union of title/text terms, then write their weights to `term_chunks`.
4. Increment the chunk count before requesting the next chunk.

Keep only current chunk data and term sets in Python. Do not collect all chunks,
all terms, or all document IDs. Input document metadata is consistent even when
chunks are interleaved or the document already exists. Chunk identities are new;
duplicates may raise `sqlite3.IntegrityError`. Ignore duplicate document/access
identities only, not duplicate chunks. Empty input returns zero. Chunks with no
searchable words still need identity/text rows and count toward the result.

Bind caller values with placeholders. For example, in an unrelated table:

```python
cursor = connection.execute('INSERT INTO labels(name) VALUES (?)', (label,))
new_id = cursor.lastrowid
```

The comma creates a one-item tuple. `executemany` accepts generated row tuples.
The caller owns commit/rollback/close. One large transaction still has database
costs; a production ingestion pipeline needs an explicit commit/recovery policy.
This task appends unique chunks, not document updates or metadata conflicts.

## Checkpoint 2: rank readable chunks in SQL

Edit `search_index.py`; run `python -m pytest -q tests/test_query.py`.
Tests seed term weights independently so your builder need not be solved first.

Validate integer `limit` in 1..100 before handling an empty query. Normalize query
terms once with `terms()`. Empty terms return `[]`; input has at most 32 distinct
terms. Query terms use OR matching, each contributing once.

Look up `term_chunks` by tenant and query terms. Join `chunks` using `chunk_pk`
and tenant, then `documents` using tenant/document identity. A result must belong
to the caller's tenant and have either document public visibility or a matching
`document_access` row for this user. Use `EXISTS` so multiple allowed users do not
multiply score contributions.

Group by chunk database ID and sum matching weights. Order by score descending,
then document ID and chunk ID ascending. Chunk IDs sort as strings, so `"10"`
precedes `"2"` in a tie. Apply SQL LIMIT last. Return IndexedHit records, reading
at most limit rows into Python. Do not read `chunk_texts`, re-tokenize saved text,
sort all candidates in Python or modify the connection.

Generate only IN-clause placeholder syntax; bind all caller values. Inspect
`EXPLAIN QUERY PLAN`: it should search on tenant and term. The tests check that
lookup and count final rows transferred to Python. Frequent words can still
match many chunks and require database grouping/sorting or temporary files.

## Checkpoint 3: produce chunks from streamed words

Edit `chunk_documents.py`; run `python -m pytest -q tests/test_chunks.py`.

Each `ExtractedDocument` pairs shared `Document` metadata with a one-pass `words`
iterator. Validate `max_words >= 1` before consuming input (on first iteration is
fine). Add words to a small list. At max_words, join with single spaces and yield
a DocumentChunk immediately, before requesting another word. Reset the buffer and
increment its string chunk ID. Flush a final short chunk, skip empty streams, and
restart numbering at `"0"` for the next document. Preserve case and punctuation.

The supplied reader bounds individual words; tests also use guarded iterators to
catch whole-file buffering or reading ahead. Fixed word groups can cut sentences
and separate evidence. Edits can shift every subsequent chunk number. Production
citations need versioned identity or offsets plus retained content, not merely a
counter that happens to match an earlier run.

## Try the connected pipeline

After solving the three files, run `python demo.py`. The demo writes synthetic
text incrementally, opens each source file lazily, reads bounded blocks, groups
words into chunks, persists them, searches and prints selected text ready for
context. The caller keeps each file open while its word iterator is consumed.
The demo does not call a model or run context selection.

`load_chunks` preserves hit order and rechecks document access before returning
text. It adapts results to the existing context exercise's `Chunk` boundary
record, whose access fields carry this caller's checked scope. Those fields are
not duplicate permissions stored in the index. The context exercise preserves
source document/chunk IDs in citations and applies a separate word budget and
per-document cap.

## Edits, deletion and saved practice

Production updates replace one document's indexed chunks; deletions remove them.
Both must account for revision ordering, retries and permission freshness. This
pack implements initial ingestion only. Opening the database does not rebuild
it, and searches never invoke the builder.

This revision replaces the earlier whole-document `SearchUnit` contract with
streamed chunks and normalized metadata. Activity IDs and saved drafts remain.
Export an older draft before using Reset to load the new starter. Existing local
practice databases using `units/contents/grants/postings` are not migrated; use a
new database path for this revised pack. The demo already creates a fresh one.

Technical references: [SQLite query planning](https://www.sqlite.org/queryplanner.html),
[Python SQLite API](https://docs.python.org/3/library/sqlite3.html),
[SQLite temporary storage](https://www.sqlite.org/tempfiles.html), and
[FTS5 storage and updates](https://www.sqlite.org/fts5.html).
