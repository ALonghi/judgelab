"""After solving all three checkpoints: python demo.py. All data is synthetic."""
from pathlib import Path
from tempfile import TemporaryDirectory
from models import Document, ExtractedDocument
from source_words import iter_words
from storage import load_chunks, open_index
from build_index import build_index
from search_index import search_index
from chunk_documents import chunk_documents


def documents(directory):
    # Files are opened lazily and remain open while their words are consumed.
    for tenant, key, title in [("a", "d1", "Lease notice"),
                               ("a", "d2", "Checklist"),
                               ("b", "private", "Other tenant")]:
        with (directory / f"{key}.txt").open(encoding="utf-8") as source:
            yield ExtractedDocument(Document(tenant, key, title, True), iter_words(source))


def main():
    with TemporaryDirectory(prefix="judgelab-index-demo-") as directory:
        directory = Path(directory)
        # Write incrementally too: no complete source body is constructed.
        with (directory / 'd1.txt').open('w', encoding='utf-8') as target:
            for _ in range(1000):
                target.write('Notice period is thirty days.\n')
        (directory / 'd2.txt').write_text('Send notice early', encoding='utf-8')
        (directory / 'private.txt').write_text('Other tenant text', encoding='utf-8')
        connection = open_index(directory / 'search.sqlite')
        try:
            with connection:
                count = build_index(connection, chunk_documents(documents(directory), max_words=200))
            print('Chunks indexed:', count)
            hits = search_index(connection, 'notice', tenant_id='a', user_id='u', limit=3)
            print('Matches:', [(h.document_id, h.chunk_id, h.score) for h in hits])
            for chunk in load_chunks(connection, hits, tenant_id='a', user_id='u'):
                print('  Ready for context:', chunk.document_id, chunk.chunk_id, repr(chunk.text))
        finally:
            connection.close()


if __name__ == '__main__':
    main()
