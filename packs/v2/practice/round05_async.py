"""Optional deeper extension. Read prompts/05_async.md, then run:
    python -m pytest -q tests/test_05_async.py -x
Suggested time: 30-40 minutes. Explore concurrency and failure handling.
"""
from collections.abc import Awaitable, Callable, Mapping
from practice.models import Candidate, FederatedResult


type SearchSource = Callable[[str], Awaitable[list[Candidate]]]


async def federated_search(
    query: str,
    sources: Mapping[str, SearchSource],
    *,
    max_concurrency: int = 3,
    timeout_s: float = 1.0,
) -> FederatedResult:
    """Fan out a query to fake search sources, then merge their results.

    TODO:
    - Validate max_concurrency >= 1 and finite timeout_s > 0 before doing work.
      Assume int and float argument types, respectively. Raise ValueError.
    - Call every supplied source exactly once with query.
    - Run concurrently, but cap active source calls at max_concurrency.
    - Timeout starts when a call acquires its slot, NOT while queued for one.
    - Each normal Exception/timeout marks that source failed; other sources
      should still complete. failed_sources is a lexicographically sorted tuple.
    - Merge hits by (tenant_id, document_id), retaining the highest score.
      Sort descending score, then ascending tenant_id and document_id.
    - Empty sources -> FederatedResult((), ()).
    - Cancellation of this operation must propagate; all owned source tasks
      must be cancelled/awaited before this function finishes unwinding.

    Sources are already permission-scoped by a trusted upstream layer. Their
    returned scores are finite and comparable ONLY for this toy exercise.
    Source count is small; a worker pool for millions of tasks is not required.
    Use only the standard library. No real I/O services.
    """
    raise NotImplementedError("Round 5: implement federated_search")
