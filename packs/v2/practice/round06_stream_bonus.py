"""Bonus: general coding with a streaming input. Read prompts/06_stream_bonus.md.
    python -m pytest -q tests/test_06_stream_bonus.py -x
Suggested time: 20-30 minutes. No asyncio; no real model/API.
"""
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class StreamEvent:
    kind: Literal["token", "citation"]
    value: str


class InvalidStreamEvent(ValueError):
    """Bad JSON or an event that does not match the exercise schema."""


def parse_events(chunks: Iterable[str]) -> Iterator[StreamEvent]:
    """Parse newline-delimited JSON incrementally, independent of chunk boundaries.

    TODO:
    - Input strings may split a JSON line anywhere or contain several lines.
    - Each nonblank line must be an object with EXACTLY keys "type" and "value".
      type is "token" or "citation"; value is a string (empty is allowed).
    - Yield StreamEvent(type, value) immediately when a complete line is ready.
      Do not read future input unnecessarily or buffer the whole stream.
    - Ignore blank lines. Handle LF and CRLF input.
    - On clean EOF, parse one final nonblank line even without a final newline.
    - Invalid JSON/schema -> InvalidStreamEvent; previously yielded events stay
      yielded. Exceptions raised by the input iterable propagate unchanged.
    - Unicode text must be preserved. Input is already decoded str, not bytes.

    An event with value="[doc-7]" is just a string here; verifying citation access
    and provenance belongs to a separate layer, not this transport parser.
    """
    # Keep the starter a generator so callers use the intended public shape.
    # Replace this body, including the empty yield-from, with your implementation.
    raise NotImplementedError("Bonus: implement parse_events")
    yield from ()
