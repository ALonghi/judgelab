"""Reference checkpoint 3: group source words without reading ahead."""
from collections.abc import Iterable, Iterator
from models import DocumentChunk, ExtractedDocument


def chunk_documents(documents: Iterable[ExtractedDocument], *,
                    max_words: int) -> Iterator[DocumentChunk]:
    if max_words < 1:
        raise ValueError("max_words must be positive")
    for source in documents:
        words = []
        index = 0
        for word in source.words:
            words.append(word)
            if len(words) == max_words:
                yield DocumentChunk(source.document, str(index), " ".join(words))
                words = []
                index += 1
        if words:
            yield DocumentChunk(source.document, str(index), " ".join(words))
