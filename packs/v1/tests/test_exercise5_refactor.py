import time

import pytest

import practice.exercise5_refactor as ex


def test_mutable_default_state_does_not_leak():
    assert ex.add_audit_tag("a") == ["a"]
    assert ex.add_audit_tag("b") == ["b"]


@pytest.mark.asyncio
async def test_process_items_preserves_order():
    assert await ex.process_items(["a", "b", "c"]) == ["A", "B", "C"]


@pytest.mark.asyncio
async def test_process_items_is_concurrent():
    started = time.perf_counter()
    result = await ex.process_items(["a", "b", "c", "d", "e"])
    elapsed = time.perf_counter() - started

    assert result == ["A", "B", "C", "D", "E"]
    assert elapsed < 0.30, f"took {elapsed:.3f}s; likely still serial/blocking"


@pytest.mark.asyncio
async def test_one_failure_does_not_fail_batch(monkeypatch):
    original = ex.expensive_lookup

    async def sometimes_fails(item_id: str) -> str:
        if item_id == "bad":
            raise RuntimeError("boom")
        return await original(item_id)

    monkeypatch.setattr(ex, "expensive_lookup", sometimes_fails)

    assert await ex.process_items(["a", "bad", "c"]) == ["A", None, "C"]
