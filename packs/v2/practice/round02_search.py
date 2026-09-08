"""Core coding exercise. Read prompts/02_search.md, then run:
    python -m pytest -q tests/test_02_search.py -x
Suggested time: 25-35 minutes. This module is independent of Round 1.
"""
from collections.abc import Iterable
from practice.models import Document, SearchHit
from practice.text import terms  # Provided; no need to implement a tokenizer.


def search_documents(
    documents: Iterable[Document],
    query: str,
    *,
    tenant_id: str,
    user_id: str,
    categories: frozenset[str] | None = None,
    limit: int = 20,
) -> list[SearchHit]:
    """Implement deterministic, permission-aware toy search.

    TODO, in increments:
    1. Validate limit: 1 <= limit <= 100, otherwise raise ValueError, even on
       empty input/query. You can assume the supplied limit is an int.
    2. A document is visible only if its tenant matches AND (public OR the user
       is in allowed_users). Public means public WITHIN the tenant.
    3. categories=None means no category filter; an empty set matches nothing;
       otherwise require at least one category in common (OR semantics).
    4. For each DISTINCT query token: +3 if in title, +1 if in body.
       A token present in both contributes 4. Repetition adds no extra points.
       Use the supplied terms() helper. Matching is whole-token, not substring.
    5. Exclude score=0. An empty/punctuation-only query returns [].
    6. Sort by descending score, then ascending document_id. Take limit LAST.
    7. Map to SearchHit. Do not mutate documents. Input identities are unique.

    No external search engine, embeddings, HTTP, or LLM calls are needed.
    This scoring rule is a simplified practice specification.
    """
    raise NotImplementedError("Round 2: implement search_documents")
