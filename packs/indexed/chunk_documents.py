"""Checkpoint 3. Group streamed source words into searchable chunks."""
from collections.abc import Iterable, Iterator
from models import DocumentChunk, ExtractedDocument


def chunk_documents(documents: Iterable[ExtractedDocument], *,
                    max_words: int) -> Iterator[DocumentChunk]:
    """Yield bounded chunks from one-pass word iterators, in source order.

    max_words is an int; raise ValueError if <1 before consuming documents
    (validation may occur when iteration starts). Each source supplies shared
    Document metadata and words: nonempty whitespace-delimited strings with
    case/punctuation intact. The supplied iter_words() reader limits word size.
    Retain at most max_words words. Join them with single spaces and yield
    immediately when full, BEFORE requesting another word. Flush a final short
    chunk. Skip empty word streams. Number chunks '0', '1', ... per document.
    Each DocumentChunk refers to the source Document; do not copy title/access
    into new per-chunk metadata or buffer the entire source/word iterator.
    Finish this document before requesting the next. Do not mutate inputs.
    With bounded source words, memory is independent of total file size/count.
    File decoding, PDF/OCR and sentence-aware boundaries are outside this task.
    """
    raise NotImplementedError("Group streamed words into identified chunks")
