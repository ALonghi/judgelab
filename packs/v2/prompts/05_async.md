# Round 5 — query several sources with bounded concurrency

**Timebox: 30–40 minutes. Optional deeper extension.**
Implement `practice/round05_async.py`.
Run `python -m pytest -q tests/test_05_async.py -x`.

The job ad values concurrent/asynchronous code, but the invitation does not say it
will be tested. Prioritize the plain-Python rounds before this one.

## Contract

You receive a mapping from source name to async search function. Each accepts a
query and returns Candidate objects. Functions are fakes, already scoped to trusted
permissions. Scores are finite/comparable by assumption for this task only.

Invoke each source once, concurrently up to max_concurrency. Each active call gets
its own timeout_s budget. Waiting for a concurrency slot does NOT spend that budget.
Normal exceptions and timeouts are partial failures: keep successful hits, and
return the failed source names in lexicographic order.

Merge duplicate `(tenant_id, document_id)` hits using the largest score. Sort by
score descending, then tenant and ID ascending. Return immutable tuple fields in
FederatedResult. An empty source mapping returns empty fields.

Validate max_concurrency >= 1 and finite positive timeout_s before doing any work,
including for empty sources. The source count is small: a task per source is an
acceptable first version. No threads or network libraries are needed.

## Extension: cancellation

When the caller cancels, propagate cancellation and ensure owned child work has
finished cancellation/cleanup before the operation exits. Do not convert a cancelled
request to an apparently successful empty response.

Tests use events to check overlap rather than fragile speed benchmarks. Watchdogs
make serial implementations and hanging cancellation fail within a bounded time.

## Architecture follow-up

Are scores from different real search systems comparable? Should partial failure
be silent? Where would permissions be enforced in the real fan-out path? What is
the difference between limiting active work and limiting the number of queued tasks?
How would you handle a provider rate limit shared across replicas?
