# Original Round 2 tests from the V2 pack; imports adapted for this standalone folder.
import pytest
from models import Document, SearchHit
from exercise import search_documents


def doc(key, title="", text="", *, tenant="a", public=True, allowed=(), cats=()):
    return Document(tenant, key, 1, title, text, frozenset(cats), frozenset(allowed), public)


def search(data, query="notice", **kwargs):
    return search_documents(data, query, tenant_id="a", user_id="alice", **kwargs)


def test_search_title_and_body_score_once_per_query_term():
    data = [doc("1", "NOTICE notice", "notice notice")]
    assert search(data, "notice notice") == [SearchHit("1", "NOTICE notice", 4)]


def test_search_multiple_terms_or_matches():
    data = [doc("1", "Termination", "notice"), doc("2", "", "notice")]
    assert search(data, "termination notice") == [SearchHit("1", "Termination", 4),
                                                 SearchHit("2", "", 1)]


def test_search_whole_token_not_substring():
    data = [doc("1", "notices"), doc("2", "NOTICE!"), doc("3", "unrelated")]
    assert [h.document_id for h in search(data)] == ["2"]


def test_search_ties_sorted_by_document_id():
    assert [h.document_id for h in search([doc("z", "notice"), doc("a", "notice")])] == ["a", "z"]


def test_search_tenant_and_user_permissions():
    data = [doc("other", "notice", tenant="b", public=True),
            doc("bob", "notice", public=False, allowed=("bob",)),
            doc("alice", "notice", public=False, allowed=("alice",)),
            doc("public", "notice"), doc("nobody", "notice", public=False)]
    assert [h.document_id for h in search(data)] == ["alice", "public"]


def test_search_limits_after_permissions_and_ranking():
    data = [doc("secret", "notice", "notice", public=False),
            doc("low", "", "notice"), doc("high", "notice")]
    assert search(data, limit=1) == [SearchHit("high", "notice", 3)]


def test_search_category_or_filter():
    data = [doc("1", "notice", cats=("contract",)), doc("2", "notice", cats=("memo",)),
            doc("3", "notice", cats=("litigation",)), doc("4", "notice")]
    assert [h.document_id for h in search(data, categories=frozenset({"memo", "contract"}))] == ["1", "2"]
    assert len(search(data, categories=None)) == 4
    assert search(data, categories=frozenset()) == []


@pytest.mark.parametrize("query", ["", "   ", "!?", "absent"])
def test_search_no_query_or_no_matches(query):
    assert search([doc("1", "notice")], query) == []


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_search_invalid_limit_even_on_empty_input(limit):
    with pytest.raises(ValueError):
        search([], "", limit=limit)


def test_search_accepts_generator_and_keeps_input_unchanged():
    data = [doc("2", "notice"), doc("1", "notice")]
    before = list(data)
    assert [h.document_id for h in search(iter(data))] == ["1", "2"]
    assert data == before


def test_search_empty_corpus():
    assert search([]) == []
