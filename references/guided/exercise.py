"""Guided version of Round 2. Edit this file only to start.

Follow README.md. Models, tokenization, examples, and tests are provided.
This preserves the V2 search contract; helpers are an added teaching scaffold.
These are toy search contracts for learning and experimentation.
"""
from collections.abc import Iterable

from models import Document, SearchHit
from text_tools import terms


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


def can_read(document: Document, *, tenant_id: str, user_id: str) -> bool:
    if document.tenant_id != tenant_id:
        return False
    return document.public or user_id in document.allowed_users


def matches_categories(document: Document, categories: frozenset[str] | None) -> bool:
    if categories is None:
        return True
    return bool(document.categories & categories)


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
