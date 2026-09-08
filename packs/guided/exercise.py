"""Guided version of Round 2. Edit this file only to start.

Follow README.md. Models, tokenization, examples, and tests are provided.
This preserves the V2 search contract; helpers are an added teaching scaffold.
These are toy search contracts for learning and experimentation.
"""
from collections.abc import Iterable

from models import Document, SearchHit
from text_tools import terms


def score_document(document: Document, query_terms: set[str]) -> int:
    """STAGE 1: score ONE document. Ignore all permissions/categories here.

    For each distinct query term:
    - +3 when present in the title;
    - independently, +1 when present in the body (document.text).
    - A word in BOTH contributes 4, not 3.
    - Repetition in query/title/body never increases its contribution.
    - Whole tokens only: 'notice' must not match 'notices'.
    - Empty query_terms => 0.

    Example:
      query_terms = {'termination', 'notice'}
      title = 'Termination clause'
      text = 'Notice of termination.'
      result = 5: termination 3+1, notice 0+1.

    TODO 1: Convert title and text with the provided terms() function.
    TODO 2: Accumulate the score. An explicit loop is fine.
    TODO 3: Return an int. Do not modify the document or query_terms.

    Test only this stage:
      python -m pytest -q tests/test_stages.py -k stage1 -x
    """
    raise NotImplementedError("Stage 1: implement score_document")


def can_read(document: Document, *, tenant_id: str, user_id: str) -> bool:
    """STAGE 2: decide whether this user may read ONE document.

    Tenant is the customer firm. Identity here is already trusted/authenticated.
    - A different tenant is ALWAYS rejected, even when public=True and even
      when user_id happens to appear in that other tenant's allowed_users.
    - Within the right tenant, public=True makes the document readable.
    - Otherwise user_id must appear in allowed_users.
    - No allowed users + public=False => unreadable.

    TODO: Express those gates with early returns or one parenthesized expression.
    Do not consult relevance, categories, or document.version here.

    Test:
      python -m pytest -q tests/test_stages.py -k stage2 -x
    """
    raise NotImplementedError("Stage 2: implement can_read")


def matches_categories(
    document: Document,
    categories: frozenset[str] | None,
) -> bool:
    """STAGE 3: check an optional category filter.

    These are already assigned labels; you are not implementing a classifier.
    - None means no filter, so every document matches this helper.
    - An empty frozenset means match nothing, NOT 'no filter'.
    - Otherwise, at least one document category must be in the requested set.
    - Names are exact/case-sensitive. This is OR, not AND.

    TODO: Treat None explicitly. Then determine whether any label is shared.
    Return a bool, not a set.

    Test:
      python -m pytest -q tests/test_stages.py -k stage3 -x
    """
    raise NotImplementedError("Stage 3: implement matches_categories")


def search_documents(
    documents: Iterable[Document],
    query: str,
    *,
    tenant_id: str,
    user_id: str,
    categories: frozenset[str] | None = None,
    limit: int = 20,
) -> list[SearchHit]:
    """STAGE 4: compose the helpers into the original Round 2 contract.

    TODO A: Validate 1 <= limit <= 100. Raise ValueError otherwise. Do this
      BEFORE early returns for an empty query/input/filter. limit is an int.
    TODO B: Tokenize query ONCE. Empty/punctuation-only query => [].
    TODO C: Visit each document once. Use your two filter helpers. For eligible
      documents compute a score and keep positive-scoring SearchHit records.
    TODO D: Sort hits by score descending, then document_id ascending.
    TODO E: Apply limit LAST, and return a list.

    Inputs already have unique (tenant_id, document_id) identities. No version
    selection or deduplication is required. documents can be a generator:
    do not require len(), indexing, or a second pass over it. Do not mutate it.

    A high-scoring inaccessible document must not take a result slot away from
    a lower-scoring accessible document. Do not sort/limit globally then filter.

    Stage 4 smoke tests:
      python -m pytest -q tests/test_stages.py -k stage4 -x
    Original V2 acceptance tests:
      python -m pytest -q tests/test_original_contract.py -x
    """
    raise NotImplementedError("Stage 4: implement search_documents")
