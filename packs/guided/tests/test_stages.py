"""Teaching checkpoints, separate from the unchanged original search contract.

-k stage1, stage2, stage3, or stage4 runs only that stage. Remove -k to run them all.
No timing-based tests or network calls.
"""
import pytest

from exercise import score_document, can_read, matches_categories, search_documents
from models import Document, SearchHit
from text_tools import terms
from examples import DOCUMENTS


def make_doc(title="", text="", *, tenant="firm-a", public=False, users=(), cats=()):
    return Document(tenant, "example", 1, title, text, frozenset(cats), frozenset(users), public)


@pytest.mark.parametrize(
    "title,text,query,expected",
    [
        ("Unrelated", "Other words", "notice", 0),
        ("Notice period", "Unrelated", "notice", 3),
        ("Policy", "Give notice", "notice", 1),
        ("Notice period", "Give notice", "notice", 4),
        ("Termination clause", "Notice of termination.", "termination notice", 5),
        ("NOTICE notice", "notice notice", "notice notice", 4),
        ("Notices", "Noticed", "notice", 0),
        ("NOTICE!", "notice?", "NoTiCe", 4),
        ("Notice", "notice", "!?", 0),
    ],
    ids=["no-match", "title-only", "body-only", "both-fields", "multiple-terms",
         "repetition", "whole-tokens", "case-punctuation", "empty-query"],
)
def test_stage1_scores(title, text, query, expected):
    query_terms = terms(query)
    before = set(query_terms)
    result = score_document(make_doc(title, text), query_terms)
    assert type(result) is int
    assert result == expected
    assert query_terms == before, "Do not consume/mutate the query set across documents."


@pytest.mark.parametrize(
    "tenant,public,users,expected",
    [
        ("firm-a", True, (), True),
        ("firm-a", False, ("alice",), True),
        ("firm-a", False, ("bob",), False),
        ("firm-a", False, (), False),
        ("firm-b", True, (), False),
        ("firm-b", False, ("alice",), False),
        ("firm-a", True, ("bob",), True),
    ],
    ids=["same-public", "same-authorized", "same-wrong-user", "same-no-user",
         "other-public", "other-matching-user", "public-overrides-user-list-within-tenant"],
)
def test_stage2_permissions(tenant, public, users, expected):
    result = can_read(make_doc(tenant=tenant, public=public, users=users),
                      tenant_id="firm-a", user_id="alice")
    assert result is expected


@pytest.mark.parametrize(
    "doc_cats,requested,expected",
    [
        (("contract",), None, True),
        ((), None, True),
        (("contract",), frozenset(), False),
        (("contract",), frozenset({"memo", "contract"}), True),
        (("contract",), frozenset({"memo"}), False),
        ((), frozenset({"memo"}), False),
        (("Memo",), frozenset({"memo"}), False),
    ],
    ids=["none", "none-on-unlabelled", "empty", "any-overlap", "no-overlap",
         "unlabelled", "case-sensitive"],
)
def test_stage3_categories(doc_cats, requested, expected):
    assert matches_categories(make_doc(cats=doc_cats), requested) is expected


def test_stage4_end_to_end_top_two():
    assert search_documents(DOCUMENTS, "termination notice", tenant_id="firm-a",
                            user_id="alice", limit=2) == [
        SearchHit("a", "Termination letter", 4),
        SearchHit("b", "Termination policy", 4),
    ]


def test_stage4_filter_before_limit():
    assert search_documents(DOCUMENTS, "termination notice", tenant_id="firm-a",
                            user_id="alice", categories=frozenset({"memo"}), limit=1) == [
        SearchHit("c", "Employment memo", 2),
    ]


def test_stage4_no_filter_is_not_empty_filter():
    all_hits = search_documents(DOCUMENTS, "termination notice", tenant_id="firm-a", user_id="alice")
    assert [hit.document_id for hit in all_hits] == ["a", "b", "c"]
    assert search_documents(DOCUMENTS, "termination notice", tenant_id="firm-a", user_id="alice",
                            categories=frozenset()) == []


def test_stage4_query_repetition_does_not_change_results():
    kwargs = {"tenant_id": "firm-a", "user_id": "alice"}
    assert search_documents(DOCUMENTS, "termination notice notice", **kwargs) == search_documents(
        DOCUMENTS, "termination notice", **kwargs)


def test_stage4_validate_before_short_circuits():
    with pytest.raises(ValueError):
        search_documents([], "", tenant_id="firm-a", user_id="alice", limit=0,
                         categories=frozenset())
