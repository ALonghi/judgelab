"""Async scenarios run via asyncio.run(), so pytest-asyncio is not required.
Events check actual overlap/cancellation; watchdogs only stop broken code hanging.
"""
import asyncio
import math
import pytest
from practice.models import Candidate, FederatedResult
from practice.round05_async import federated_search


def test_async_empty_sources():
    assert asyncio.run(federated_search("q", {})) == FederatedResult((), ())


def test_async_calls_once_merges_best_score_and_sorts_deterministically():
    async def scenario():
        calls = []
        async def first(query):
            calls.append(("first", query))
            return [Candidate("a", "d1", .7), Candidate("a", "d2", .8)]
        async def second(query):
            calls.append(("second", query))
            return [Candidate("a", "d1", .9), Candidate("b", "d1", .8), Candidate("a", "d3", .8)]
        result = await federated_search("notice", {"first": first, "second": second})
        assert sorted(calls) == [("first", "notice"), ("second", "notice")]
        assert result == FederatedResult((Candidate("a", "d1", .9), Candidate("a", "d2", .8),
                                          Candidate("a", "d3", .8), Candidate("b", "d1", .8)), ())
    asyncio.run(scenario())


def test_async_partial_failure_is_visible_and_does_not_erase_successes():
    async def scenario():
        async def good(query):
            return [Candidate("a", "ok", 1.0)]
        async def bad(query):
            raise RuntimeError("source down")
        result = await federated_search("q", {"z": bad, "good": good, "a": bad})
        assert result == FederatedResult((Candidate("a", "ok", 1.0),), ("a", "z"))
    asyncio.run(scenario())


def test_async_runs_in_parallel_and_respects_cap():
    async def scenario():
        started = 0
        active = 0
        peak = 0
        overlap = asyncio.Event()
        release = asyncio.Event()
        async def source(query):
            nonlocal started, active, peak
            started += 1
            active += 1
            peak = max(peak, active)
            if active == 2:
                overlap.set()
            try:
                await release.wait()
                return []
            finally:
                active -= 1
        task = asyncio.create_task(federated_search("q", {str(i): source for i in range(6)},
                                                    max_concurrency=2, timeout_s=5))
        try:
            await asyncio.wait_for(overlap.wait(), 2)
            assert peak == 2, "More than two source calls active"
            release.set()
            await asyncio.wait_for(task, 2)
            assert started == 6
            assert peak == 2
            assert active == 0
        finally:
            release.set()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    asyncio.run(scenario())


def test_async_timeout_cleans_up_and_queue_wait_does_not_use_call_budget():
    async def scenario():
        blocker = asyncio.Event()
        closed = asyncio.Event()
        async def slow(query):
            try:
                await blocker.wait()
                return []
            finally:
                closed.set()
        async def good(query):
            return [Candidate("a", "ok", 1.0)]
        try:
            # With concurrency=1, good must wait for slow's timeout, and must then
            # get its OWN complete timeout budget rather than timing out in queue.
            result = await asyncio.wait_for(federated_search("q", {"slow": slow, "good": good},
                                                max_concurrency=1, timeout_s=.05), 2)
            assert result == FederatedResult((Candidate("a", "ok", 1.0),), ("slow",))
            assert closed.is_set()
        finally:
            blocker.set()
    asyncio.run(scenario())


def test_async_caller_cancellation_propagates_and_no_source_is_left_running():
    async def scenario():
        started = 0
        closed = 0
        active = 0
        began = asyncio.Event()
        release = asyncio.Event()
        async def source(query):
            nonlocal started, closed, active
            started += 1
            active += 1
            began.set()
            try:
                await release.wait()
                return []
            finally:
                active -= 1
                closed += 1
        task = asyncio.create_task(federated_search("q", {"one": source, "two": source}, timeout_s=10))
        try:
            await asyncio.wait_for(began.wait(), 2)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, 2)
            assert active == 0, "Child work outlived its cancelled parent"
            assert started == closed
        finally:
            release.set()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    asyncio.run(scenario())


@pytest.mark.parametrize("cap,timeout", [(0, 1.), (-1, 1.), (1, 0.), (1, -.1),
                                         (1, math.inf), (1, math.nan)])
def test_async_validates_before_work_even_for_empty_sources(cap, timeout):
    with pytest.raises(ValueError):
        asyncio.run(federated_search("q", {}, max_concurrency=cap, timeout_s=timeout))
