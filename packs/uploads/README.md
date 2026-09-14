# Large uploads, batches and searchable text

A records portal accepts a 4 GiB file over a connection that sometimes drops.
Another import contains 2,000 files. Users need individual progress and a way to
retry failures without sending successful files again. Complete the three Python
checkpoints locally; no cloud account or multi-gigabyte fixture is needed.

## 1. Resume one file

Edit `upload.py`; run `python -m pytest -q tests/test_upload.py`.

The API would authenticate the caller, allocate a tenant-scoped upload session
and return permission to transfer bytes to storage. The transfer client sends
bounded parts. The server reports how many bytes it has acknowledged. After an
interruption, that offset tells the client where to resume. Only a completed
object is eligible for indexing.

In this exercise `UploadSession` in `storage.py` is supplied. It appends validated
parts to a local file; `offset` is the acknowledged length. Given `abcdefgh`,
size 8 and part size 3, the first call might store `abc` then lose the reply.
A second call sees offset 3, seeks there, sends `def` and `gh`, and completes.
Starting at zero would repeat the prefix. A short read is not end-of-file unless
it returns empty bytes. Use `read(size)` and `seek(offset)` on the binary source.

A checksum detects damaged transfer data. The supplied adapter checks SHA-256
for each part before writing it. This does not prove that a reopened source is
unchanged: the caller guarantees immutable source identity between attempts.
A real protocol needs an immutable source fingerprint/version and final integrity
verification. Multipart object-store APIs also use part numbers and completion
manifests; this contiguous-offset adapter intentionally simplifies that protocol.
Ordinary failures retain parts. Explicit abandonment calls the supplied `abort()`;
a production expiry policy must reclaim forgotten uploads.

## 2. Upload a batch without allocating a task per file

Edit `batch.py`; run `python -m pytest -q tests/test_batch.py`.

A batch coordinator claims IDs from a manifest and delegates each upload. Three
workers can each own one transfer. When a worker finishes, it claims the next ID.
For `[a, b, c]`, b may finish first, but the report still follows a, b, c. If b
fails, a and c can succeed. A retry request selects b and reuses b's upload session.
A semaphore around 100,000 already-created tasks limits network calls but still
allocates those tasks. Here the worker count bounds both.

The iterable is synchronous and shared by tasks on one event loop. Claim an ID
and reserve its result position before awaiting the uploader; no other task can
interleave that short synchronous section. `asyncio.gather` waits for children;
a `finally` block must cancel and await remaining children after failure or
cancellation. Ordinary file errors become results. Cancellation and a broken
manifest propagate to the caller. The uploader owns resumption; the coordinator
does not invent an automatic retry policy.

This report retains O(files) metadata. Production imports with millions of
entries need durable per-file status and paginated reports. The memory used by
transfer buffers is approximately active files × active parts per file × part
size, plus adapter overhead. Independent limits for files and parts multiply.
Per-process limits do not enforce a tenant-wide allowance across service replicas.

## 3. Extract text incrementally, then query a real index

Edit `extract.py`; run `python -m pytest -q tests/test_extract.py`.
After checkpoints 1 and 3, run `python demo.py`.

The demo stores an upload on disk, reads it in small byte blocks, extracts text
sections, and writes those sections to SQLite FTS5. It closes and reopens the
index before searching for `notice`, then deletes the document with a newer
revision. The index is derived data; the stored original can rebuild it.

A network/storage block can end halfway through the UTF-8 encoding of `é`.
`codecs.getincrementaldecoder('utf-8')` retains incomplete character bytes between
calls. Flush with `final=True` at EOF to reject a truncated character. Retain only
the unfinished LF-delimited line between blocks. For `b'lease no'` followed by
`b'tice\nnext'`, emit `lease notice` and then `next` at EOF. This preserves words
within each section, unlike cutting text at arbitrary upload-part boundaries.
Empty LF lines are omitted; spaces and carriage returns are retained.

Input blocks are bounded by the caller. A line exceeding `max_line_chars` fails
explicitly, including a long unfinished line. The limit makes this a constrained
plain-text extractor. Files with long unbroken lines need a different sectioning
policy. PDF, office-document extraction and OCR are not implemented in this pack;
they need format-specific parsers, resource limits and separate failure handling.

`indexing.py` is supplied infrastructure, not a hidden exercise solution. It uses
one SQLite transaction to publish a complete document revision. If later bytes
are invalid, rollback preserves the previous searchable revision. Equal or older
versions are skipped; the caller guarantees one immutable payload per revision.
A deletion retains the version, so delayed work cannot restore deleted text.
This single-tenant CLI does not implement user authorization. See the existing
FTS exercise for SQL permission filtering and the architecture discussion for
current permissions across asynchronous stores.

One huge extraction transaction holds a write lock and can grow the journal.
The production alternative discussed here stages sections under a new revision
in bounded writes, then atomically changes the document's active revision after
extraction succeeds. Queries must select only active revisions. Crashes leave
unpublished staging data for cleanup; old revisions remain searchable until the
switch. This alternative is discussed, not implemented by the demo.

## Architecture: a large tenant with infrequent changes

The architecture activity uses a synthetic legal-records portal: 5 million files
per tenant, less than 0.1% edited daily, 2,000-file imports, files up to 4 GiB, and
a proposed 15-minute target from completed upload to search availability for
ordinary text. These are assumptions to challenge, not facts about legal work.
Scanned documents need a separate measured OCR target. Permission revocation
must prevent access on the next request even while search indexes are catching up.

Five million files averaging 2 MB occupy about 10 TB before replicas and indexes.
At 0.1%, 5,000 files change daily. A 2,000-file batch averaging 20 MB is about
40 GB. These decimal estimates describe different workloads: storage volume,
routine changes and import bursts. Measure extracted text size, pages requiring
OCR, query concurrency and per-worker throughput before choosing capacity.

The upload API creates sessions and status records; large bytes may go directly
to object storage through narrowly scoped temporary authorization. Finalization
verifies the stored object's identity, length and integrity, then commits metadata
and pending work together. Object storage and the metadata database do not share
that transaction. An object completed before metadata commit needs reconciliation;
a browser claiming success is not sufficient evidence to enqueue extraction.

Background workers extract sections and update a managed full-text index in
bounded batches. A low update rate and a minutes-level freshness target allow
work to be scheduled and grouped, but large first imports and rebuilds still need
capacity. Indexing completion and search visibility may be separate events.
Track upload status, extraction errors, indexing status and actual searchable
revision. Retry transient failures with limits; isolate permanent failures for
inspection. Store job identity/version and safely repeat work after a crash.

Search requests select the trusted tenant and enforce current document access
before returning titles, snippets or counts. A delayed index update cannot serve
as the sole permission gate. Apply prompt denial for revocations and deletions,
then remove derived text asynchronously according to the agreed policy. Original
retention and physical erasure are separate product decisions to clarify.

Choose database full-text search if measured queries, text volume and concurrent
writes fit its capacity. A separate search service can be justified by independent
scaling, language analysis or query capabilities. Millions of file IDs alone do
not select a vendor or determine a shard count. Compare tenant-dedicated indexes
with shared tenant-filtered indexes using tenant sizes, operational overhead,
isolation and noisy-neighbor measurements. The manual index exercises teach
mechanisms; the proposed production direction uses a maintained search facility.

For a store-and-download service, finish after durable upload, metadata and access
checks. Search adds extraction, derived indexes, freshness and rebuild obligations.
Neither upload completion nor a stored filename makes file contents searchable.

## Primary references

- [S3 multipart overview](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html): parts can be transferred independently and completed or aborted. Compare its protocol with the local contiguous-offset adapter.
- [S3 upload integrity](https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity-upload.html): compare part and full-object checksums.
- [Elastic indexing guidance](https://www.elastic.co/docs/deploy-manage/production-guidance/optimize-performance/indexing-speed): benchmark bulk size and consider less frequent refresh when freshness requirements permit it.
- [SQLite FTS5](https://www.sqlite.org/fts5.html): the demo uses SQLite's built-in text index, not a Python scan.
