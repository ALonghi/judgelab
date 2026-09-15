"""Supplied bounded reader for decoded plain text, not PDF/OCR extraction."""
from collections.abc import Iterator
from typing import TextIO


def iter_words(source: TextIO, *, read_chars: int = 4096,
               max_word_chars: int = 1024) -> Iterator[str]:
    """Preserve words across reads; reject oversized words instead of buffering them.

    The caller opens/closes the decoded text stream. read() must honor its size.
    Memory retains one read block and at most max_word_chars pending characters.
    """
    if read_chars < 1 or max_word_chars < 1:
        raise ValueError("read_chars and max_word_chars must be positive")
    pending = []
    while block := source.read(read_chars):
        for char in block:
            if char.isspace():
                if pending:
                    yield "".join(pending)
                    pending.clear()
            else:
                if len(pending) == max_word_chars:
                    raise ValueError("Source word exceeds max_word_chars")
                pending.append(char)
    if pending:
        yield "".join(pending)
