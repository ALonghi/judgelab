from __future__ import annotations

import time


# This file is intentionally bad.
# Your task is to improve it while preserving the externally tested behavior.


async def expensive_lookup(item_id: str) -> str:
    """
    Pretend this is a blocking legacy SDK call.

    BUG:
    `time.sleep()` blocks the entire asyncio event loop.
    Refactor so multiple calls can make progress concurrently.

    You are allowed to:
    - introduce a synchronous helper and use asyncio.to_thread(), OR
    - replace the fake with an async equivalent for this exercise.

    In an interview, explain what you would do if the real dependency were a
    blocking DB/HTTP library versus an async-native library.
    """
    time.sleep(0.10)
    return item_id.upper()


def add_audit_tag(tag: str, tags: list[str] = []):
    """
    BUG:
    mutable default argument leaks state across calls.

    Preserve behavior:
        add_audit_tag("a") -> ["a"]
        add_audit_tag("b") -> ["b"]

    Do not make callers responsible for passing [].
    """
    tags.append(tag)
    return tags


async def process_items(item_ids: list[str]) -> list[str | None]:
    """
    Process all items concurrently.

    Requirements
    ------------
    1. Preserve input order.
    2. Run lookups concurrently.
    3. If one lookup raises a normal Exception, put None in that position.
    4. Do NOT swallow asyncio.CancelledError.
    5. The normal happy path for 5 items should take roughly one lookup duration,
       not five lookup durations.

    The starter implementation is intentionally naive.
    """
    results: list[str | None] = []
    for item_id in item_ids:
        try:
            results.append(await expensive_lookup(item_id))
        except Exception:
            results.append(None)
    return results


# Interview follow-ups
# --------------------
# - Why is `except Exception` often too broad?
# - Does asyncio.CancelledError inherit from Exception in the Python version
#   you're using? Why should you verify rather than assume?
# - What risks come with asyncio.to_thread()?
# - Would unbounded gather() be safe for 100k items?
# - How would you add bounded concurrency?
