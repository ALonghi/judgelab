# Round 1 — small transformations, precise contracts

**Timebox: 10–15 minutes.** Implement only `practice/round01_warmup.py`.
Run `python -m pytest -q tests/test_01_warmup.py -x`.

## A. Select latest document snapshots

A connector returns multiple versions of documents, in arbitrary order. Keep one
snapshot per `(tenant_id, document_id)`. Keep the highest source version; if versions
are equal, keep the last occurrence. Return winners sorted by identity.

Example: A/d1/v3, A/d1/v1, B/d1/v1 -> A/d1/v3, B/d1/v1.
Equal versions with different titles are resolved by **last input wins for this
warm-up only**. Round 4 intentionally uses stricter conflict semantics.

`documents` may be a generator. You must not rely on a second traversal. The
input is valid and versions are positive. Empty input returns an empty list.

Before coding, say which fields make a document unique and what happens on ties.
After coding, test a cross-tenant ID collision and reverse version order.

## B. Count classification metadata

Given already-deduplicated documents with category sets, count documents per
category. A contract tagged `employment` and `contract` contributes to both.
Untagged documents contribute nothing. Preserve category spelling/case.

This is aggregation over existing labels, not a classification model.

## Questions after the code works

What are the runtime and additional memory costs? Does sorting the winners change
the dominant cost? Could latest versions be emitted before the input ends without
assumptions on order? Where should real deduplication happen when workers race?
