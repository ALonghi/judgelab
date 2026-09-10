"""Run after solving the three checkpoints: python demo.py."""
from pathlib import Path
from tempfile import TemporaryDirectory
from models import Document
from storage import document_units, load_chunks, open_index
from build_index import build_index
from search_index import search_index
from chunk_documents import chunk_documents


def documents():
    yield Document("a", "d1", "Lease notice", "Notice period is thirty days", True)
    yield Document("a", "d2", "Checklist", "Send notice early", True)
    yield Document("b", "private", "Lease notice", "Other tenant", True)


def main():
    with TemporaryDirectory(prefix="judgelab-index-demo-") as directory:
        for label, units in [("Documents", document_units(documents())),
                             ("Chunks", chunk_documents(documents(), max_words=3))]:
            connection = open_index(Path(directory) / f"{label}.sqlite")
            try:
                with connection:
                    build_index(connection, units)
                hits = search_index(connection, "notice", tenant_id="a", user_id="u", limit=3)
                print(label, [(h.document_id, h.chunk_id, h.score) for h in hits])
                if label == "Chunks":
                    for chunk in load_chunks(connection, hits, tenant_id="a", user_id="u"):
                        print("  Ready for context:", chunk.document_id, chunk.chunk_id, repr(chunk.text))
            finally:
                connection.close()


if __name__ == "__main__":
    main()
