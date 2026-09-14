"""Reference: incremental decoding with a bounded unfinished line."""
import codecs
from collections.abc import Iterable, Iterator


def extract_lines(blocks: Iterable[bytes], *, max_line_chars: int) -> Iterator[str]:
    if max_line_chars < 1:
        raise ValueError('max_line_chars must be positive')
    decoder = codecs.getincrementaldecoder('utf-8')('strict')
    pending = ''

    def decoded():
        for block in blocks:
            yield decoder.decode(block)
        yield decoder.decode(b'', final=True)

    for text in decoded():
        parts = (pending + text).split('\n')
        for line in parts[:-1]:
            if len(line) > max_line_chars:
                raise ValueError('Line exceeds extraction limit')
            if line:
                yield line
        pending = parts[-1]
        if len(pending) > max_line_chars:
            raise ValueError('Line exceeds extraction limit')
    if pending:
        yield pending
