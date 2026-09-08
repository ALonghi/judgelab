"""Run after completing Stage 4: python demo.py."""
from exercise import search_documents
from examples import DOCUMENTS


def main() -> None:
    print("Expected: a (4), b (4).")
    try:
        hits = search_documents(
            DOCUMENTS, "termination notice", tenant_id="firm-a", user_id="alice", limit=2,
        )
    except NotImplementedError as exc:
        print(f"Still unfinished: {exc}")
        return
    print("Actual:")
    for hit in hits:
        print(f"{hit.document_id} ({hit.score}) — {hit.title}")


if __name__ == "__main__":
    main()
