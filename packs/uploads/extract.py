"""Checkpoint 3: extract bounded text sections from UTF-8 byte blocks."""
import codecs
from collections.abc import Iterable, Iterator


def extract_lines(blocks: Iterable[bytes], *, max_line_chars: int) -> Iterator[str]:
    """Yield nonempty LF-delimited lines, preserving all other characters.

    max_line_chars is an int; reject <1 before consuming input (validation may
    happen on first iteration). Input is a one-pass iterable of bounded byte
    blocks. UTF-8 characters and lines may span blocks. Empty blocks are allowed.
    Decode strictly with an incremental decoder, including its final flush:
    malformed or truncated UTF-8 raises UnicodeDecodeError. Split on '\n' only;
    omit empty lines, retain spaces and '\r', and yield a final unterminated line.
    A line longer than max_line_chars raises ValueError. Earlier yielded lines
    remain yielded. Enforce the limit on unfinished lines as well as complete
    lines. Yield complete lines before requesting the next block. Memory must
    depend on the largest supplied block and line limit, not total file length.
    This is a bounded plain-text extractor, not a PDF parser or OCR system.
    A downstream indexing transaction must roll back if extraction later fails.
    """
    raise NotImplementedError('Decode and emit sections incrementally')
