"""Run a solved round on synthetic data: python -m practice.demo search.
Only the `search` demo needs Round 1 as well as Round 2. Tests are independent.
"""
import argparse
import asyncio
from pprint import pprint
from practice.sample_data import CHUNKS, DOCUMENTS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("round", choices=["warmup", "search", "context", "ingestion", "async", "stream"])
    args = parser.parse_args()
    try:
        if args.round == "warmup":
            from practice.round01_warmup import latest_documents, category_counts
            docs = latest_documents(iter(DOCUMENTS))
            pprint(docs)
            pprint(category_counts(docs))
        elif args.round == "search":
            from practice.round01_warmup import latest_documents
            from practice.round02_search import search_documents
            pprint(search_documents(latest_documents(DOCUMENTS), "termination notice",
                                    tenant_id="firm-a", user_id="alice"))
        elif args.round == "context":
            from practice.round03_context import build_context
            pprint(build_context(CHUNKS, tenant_id="firm-a", user_id="alice", word_budget=6))
        elif args.round == "ingestion":
            from practice.round04_ingestion import apply_event, DocumentEvent
            store = {}
            events = [DocumentEvent("firm-a", "d1", 2, "upsert", DOCUMENTS[1]),
                      DocumentEvent("firm-a", "d1", 3, "delete"),
                      DocumentEvent("firm-a", "d1", 1, "upsert", DOCUMENTS[0])]
            for event in events:
                print(event.version, apply_event(store, event))
            pprint(store)
        elif args.round == "async":
            from practice.models import Candidate
            from practice.round05_async import federated_search
            async def source(query):
                await asyncio.sleep(0)
                return [Candidate("firm-a", "d1", 0.8)]
            pprint(asyncio.run(federated_search("notice", {"one": source, "two": source})))
        else:
            from practice.round06_stream_bonus import parse_events
            pprint(list(parse_events(['{"type":"tok', 'en","value":"Hello"}\n',
                                      '{"type":"citation","value":"d1"}'])))
    except NotImplementedError as exc:
        parser.exit(1, f"TODO still open: {exc}\nImplement that round and run its tests first.\n")


if __name__ == "__main__":
    main()
