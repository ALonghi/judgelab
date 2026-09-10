"""Reference checkpoint 3: stream words into bounded groups."""
import re
from collections.abc import Iterable, Iterator
from models import Document, SearchUnit


def chunk_documents(documents: Iterable[Document], *, max_words: int) -> Iterator[SearchUnit]:
    if max_words < 1:
        raise ValueError("max_words must be positive")
    for doc in documents:
        words = []
        index = 0
        for match in re.finditer(r"\S+", doc.text):
            words.append(match.group())
            if len(words) == max_words:
                yield SearchUnit(doc.tenant_id, doc.document_id, str(index), doc.title,
                                 " ".join(words), doc.public, doc.allowed_users)
                words = []
                index += 1
        if words:
            yield SearchUnit(doc.tenant_id, doc.document_id, str(index), doc.title,
                             " ".join(words), doc.public, doc.allowed_users)
