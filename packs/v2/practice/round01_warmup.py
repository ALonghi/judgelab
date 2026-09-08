"""Start here. Read prompts/01_warmup.md, then run:
    python -m pytest -q tests/test_01_warmup.py -x
Suggested time: 10-15 minutes. No asyncio or web framework needed.
"""
from collections.abc import Iterable
from practice.models import Document


def latest_documents(documents: Iterable[Document]) -> list[Document]:
    """Keep one document per (tenant_id, document_id).

    TODO:
    - Keep the highest version; on an equal version, the LAST input wins.
    - Return winners ordered by (tenant_id, document_id), ascending.
    - Consume a one-shot iterable correctly; do not modify the input.
    - Empty input returns []. Versions are positive in this exercise.

    Do not collapse documents from different tenants with the same document_id.
    """
    raise NotImplementedError("Round 1A: implement latest_documents")


def category_counts(documents: Iterable[Document]) -> dict[str, int]:
    """Count how many input documents carry each category.

    TODO:
    - Categories are already supplied metadata; do NOT build an ML classifier.
    - Count each document once per category; preserve category strings exactly.
    - A document may contribute to several categories, or none.
    - Input is already deduplicated; no need to call latest_documents here.
    - Empty input returns {}. Output dict ordering is not assessed.
    """
    raise NotImplementedError("Round 1B: implement category_counts")
