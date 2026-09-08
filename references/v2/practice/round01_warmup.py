"""Start here. Read prompts/01_warmup.md, then run:
    python -m pytest -q tests/test_01_warmup.py -x
Suggested time: 10-15 minutes. No asyncio or web framework needed.
"""
from collections.abc import Iterable
from practice.models import Document


def latest_documents(documents: Iterable[Document]) -> list[Document]:
    winners = {}
    for document in documents:
        key = (document.tenant_id, document.document_id)
        previous = winners.get(key)
        if previous is None or document.version >= previous.version:
            winners[key] = document
    return [winners[key] for key in sorted(winners)]


def category_counts(documents: Iterable[Document]) -> dict[str, int]:
    counts = {}
    for document in documents:
        for category in document.categories:
            counts[category] = counts.get(category, 0) + 1
    return counts
