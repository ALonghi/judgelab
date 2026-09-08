"""Retrieval-to-chat exercise. Read prompts/03_context.md, then run:
    python -m pytest -q tests/test_03_context.py -x
Suggested time: 25-35 minutes. Independent of Rounds 1 and 2.
"""
from collections.abc import Iterable
from practice.models import Chunk, Citation, Context


def build_context(chunks: Iterable[Chunk], *, tenant_id: str, user_id: str,
                  word_budget: int, max_per_document: int = 2) -> Context:
    if word_budget < 0 or max_per_document < 1:
        raise ValueError("Invalid budget or per-document limit")
    seen = set()
    per_document = {}
    lines = []
    citations = []
    used = 0
    for chunk in chunks:
        if chunk.tenant_id != tenant_id:
            continue
        if not (chunk.public or user_id in chunk.allowed_users):
            continue
        words = chunk.text.split()
        if not words:
            continue
        key = (chunk.tenant_id, chunk.document_id, chunk.chunk_id)
        if key in seen:
            continue
        seen.add(key)  # Even a too-large first occurrence claims this identity.
        document_key = (chunk.tenant_id, chunk.document_id)
        if per_document.get(document_key, 0) >= max_per_document:
            continue
        if used + len(words) > word_budget:
            continue  # A smaller, lower-ranked chunk might still fit.
        label = f"[{len(citations) + 1}]"
        lines.append(f"{label} {' '.join(words)}")
        citations.append(Citation(label, chunk.document_id, chunk.chunk_id))
        used += len(words)
        per_document[document_key] = per_document.get(document_key, 0) + 1
    return Context("\n".join(lines), tuple(citations), used)
