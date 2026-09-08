"""Core coding exercise. Read prompts/02_search.md, then run:
    python -m pytest -q tests/test_02_search.py -x
Suggested time: 25-35 minutes. This module is independent of Round 1.
"""
from collections.abc import Iterable
from practice.models import Document, SearchHit
from practice.text import terms  # Provided; no need to implement a tokenizer.


def search_documents(documents: Iterable[Document], query: str, *,
                     tenant_id: str, user_id: str,
                     categories: frozenset[str] | None = None,
                     limit: int = 20) -> list[SearchHit]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    query_terms = terms(query)
    if not query_terms:
        return []
    hits = []
    for document in documents:
        if not can_read(document, tenant_id=tenant_id, user_id=user_id):
            continue
        if not matches_categories(document, categories):
            continue
        score = score_document(document, query_terms)
        if score > 0:
            hits.append(SearchHit(document.document_id, document.title, score))
    hits.sort(key=lambda hit: (-hit.score, hit.document_id))
    return hits[:limit]


def can_read(document: Document, *, tenant_id: str, user_id: str) -> bool:
    if document.tenant_id != tenant_id:
        return False
    return document.public or user_id in document.allowed_users


def matches_categories(document: Document, categories: frozenset[str] | None) -> bool:
    if categories is None:
        return True
    return bool(document.categories & categories)


def score_document(document: Document, query_terms: set[str]) -> int:
    title_terms = terms(document.title)
    body_terms = terms(document.text)
    score = 0
    for term in query_terms:
        if term in title_terms:
            score += 3
        if term in body_terms:  # Independent, NOT elif.
            score += 1
    return score
