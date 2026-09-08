# Round 2 — implement ranked search, then extend the contract

**Timebox: 25–35 minutes.** Implement `practice/round02_search.py`.
Run `python -m pytest -q tests/test_02_search.py -x`.

## Initial task

Write `search_documents(documents, query, ...)`. The provided tokenizer extracts
sets of lowercase ASCII alphanumeric tokens. For every distinct query term, award
3 points for presence in the title and 1 for presence in the body. Repeated terms
have no extra effect. Include positive scores only. Sort by score descending, then
document_id ascending. Return `SearchHit` records.

For query `termination notice`, a title containing `termination` and body
containing `notice` scores 4. A title and body both containing `notice` also score 4.
`notices` is not a match for `notice`. Punctuation-only queries yield no results.

Start with: `python -m pytest -q tests/test_02_search.py -k 'score or token or ties or terms'`.

## Extension 1: real data boundaries

Restrict results to the requested tenant. Within that tenant, a document is readable
when it is public or the supplied user appears in its allowed_users set. A public
document in another tenant is still invisible. Tenant/user values are a trusted
identity context in this exercise, not arbitrary client-supplied authentication.

Do not take the top K globally and then filter: an inaccessible top hit must not
hide a lower-scoring accessible hit.

## Extension 2: classification filters and limit

`categories=None`: no filter. Empty set: no results. Otherwise require any category
in common. Category names are exact/case-sensitive. `limit` defaults to 20 and must
be 1–100; raise ValueError for invalid limits, even on an empty corpus or query.
Return at most limit results after filtering and ranking.

## Extension 3: tests and design discussion

Add your own test for a restricted hit with a higher score than every readable hit.
Explain the full scan/sort cost before discussing an index. No index is required.
What changes with permission revocations, pagination, or multiple query languages?
How would you avoid exposing inaccessible documents via snippets or result counts?

This is a transparent practice scoring function. Do not install a vector DB or train anything.
