from __future__ import annotations
import asyncio

import time


# This file is intentionally bad.
# Your task is to improve it while preserving the externally tested behavior.


async def expensive_lookup(item_id: str) -> str:
    await asyncio.sleep(0.10)
    return item_id.upper()


def add_audit_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    if tags is None:
        tags = []
    tags.append(tag)
    return tags


async def process_items(item_ids: list[str]) -> list[str | None]:
    async def one(item_id):
        try:
            return await expensive_lookup(item_id)
        except Exception:
            return None
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(one(item_id)) for item_id in item_ids]
    return [task.result() for task in tasks]


# Interview follow-ups
# --------------------
# - Why is `except Exception` often too broad?
# - Does asyncio.CancelledError inherit from Exception in the Python version
#   you're using? Why should you verify rather than assume?
# - What risks come with asyncio.to_thread()?
# - Would unbounded gather() be safe for 100k items?
# - How would you add bounded concurrency?
