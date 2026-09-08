import json
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
    def decode(line):
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError) as error:
            raise InvalidStreamEvent("Invalid JSON") from error
        if (not isinstance(event, dict)
                or set(event) != {"type", "value"}
                or event["type"] not in ("token", "citation")
                or not isinstance(event["value"], str)):
            raise InvalidStreamEvent("Invalid event schema")
        return StreamEvent(event["type"], event["value"])

    buffer = ""
    for chunk in chunks:
        buffer += chunk
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            if line.strip():
                yield decode(line)
    if buffer.strip():
        yield decode(buffer)
