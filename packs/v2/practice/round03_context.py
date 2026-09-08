"""Retrieval-to-chat exercise. Read prompts/03_context.md, then run:
    python -m pytest -q tests/test_03_context.py -x
Suggested time: 25-35 minutes. Independent of Rounds 1 and 2.
"""
from collections.abc import Iterable
from practice.models import Chunk, Citation, Context


def build_context(
    chunks: Iterable[Chunk],
    *,
    tenant_id: str,
    user_id: str,
    word_budget: int,
    max_per_document: int = 2,
) -> Context:
    """Select already-ranked chunks and construct traceable context.

    TODO:
    - Validate word_budget >= 0 and max_per_document >= 1 (both are ints).
      Raise ValueError before consuming input if either is invalid.
    - Preserve rank/input order; do not re-sort.
    - Filter tenant/permissions BEFORE deduplication, counting, or selection.
      Visibility is the same simplified rule as Round 2.
    - Skip empty/whitespace-only text.
    - For duplicate (tenant_id, document_id, chunk_id), consider ONLY the first
      visible non-empty occurrence, even if it is later skipped for size/cap.
    - Include at most max_per_document chunks from a document.
    - Word cost is len(text.split()). Accept whole chunks only, never truncate.
      When a chunk does not fit, SKIP it and keep trying later smaller chunks.
    - Normalize selected text with " ".join(text.split()).
    - Number SELECTED chunks [1], [2], ... with no gaps. Render each line as
      "[n] normalized text" and join lines with a single newline, no trailing one.
    - Return corresponding Citation objects, in order, and words_used.
      Budget counts content words ONLY, not labels or separators.
    - No selected chunks -> Context("", (), 0).

    This is deliberately a WORD budget, not an LLM token budget. No model call.
    A valid citation mapping proves source identity, not that an answer's claims
    are entailed by the source; that is a separate evaluation problem.
    """
    raise NotImplementedError("Round 3: implement build_context")
