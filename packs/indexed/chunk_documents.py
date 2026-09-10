"""Checkpoint 3. Make independently searchable text units with source IDs."""
import re
from collections.abc import Iterable, Iterator
from models import Document, SearchUnit


def chunk_documents(documents: Iterable[Document], *, max_words: int) -> Iterator[SearchUnit]:
    r"""Yield bounded, non-overlapping chunks in document/word order.

    max_words is an int; raise ValueError if <1 before consuming documents
    (validation may occur when iteration starts). Words are whitespace-delimited
    spans; preserve their text/case/punctuation, join with single spaces.
    Skip blank bodies. Number each document's chunks '0', '1', ... .
    Copy tenant, document ID, title, public and allowed_users into every unit.
    Yield as soon as max_words words are buffered; flush a final short chunk.
    Do not read the next document before yielding this one's chunks. Do not
    split/list the entire corpus or entire document body; use re.finditer(r'\S+',
    document.text) to buffer at most max_words matched words at a time.
    A Document already contains its body string. This limits extra chunking
    memory, not the size of that source string or of an individual huge word.
    """
    raise NotImplementedError("Yield searchable chunks with provenance")
